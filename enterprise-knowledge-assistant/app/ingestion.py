import os
import re
import logging
from typing import List, Dict, Any
import pdfplumber
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "./data/documents")

def split_into_sentences(text: str) -> List[str]:
    """Splits a block of text into sentences, respecting common abbreviations."""
    # List of abbreviations to not split on
    abbreviations = [
        'Pvt.', 'Ltd.', 'e.g.', 'i.e.', 'vs.', 'Dr.', 'Mr.', 'Mrs.', 'Ms.', 
        'Jan.', 'Feb.', 'Mar.', 'Apr.', 'Oct.', 'Nov.', 'Dec.', 
        'L1.', 'L2.', 'L3.', 'SLA.', 'VPN.', 'GDPR.', 'MFA.', 'IT.', 'HR.'
    ]
    
    temp_text = text
    for abbr in abbreviations:
        placeholder = abbr.replace('.', '___DOT___')
        temp_text = temp_text.replace(abbr, placeholder)
        
    # Split on period, question mark, exclamation mark followed by whitespace
    raw_sentences = re.split(r'(?<=[.?!])\s+', temp_text)
    
    sentences = []
    for s in raw_sentences:
        s_restored = s.replace('___DOT___', '.')
        if s_restored.strip():
            # Replace multiple spaces/newlines with single space
            cleaned = " ".join(s_restored.strip().split())
            sentences.append(cleaned)
    return sentences

def extract_sentences_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text page-by-page from a PDF, detects section headers,
    and returns a list of sentences with page number and section metadata.
    """
    sentences_with_meta = []
    filename = os.path.basename(pdf_path)
    current_section = "Introduction"
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_number = page_idx + 1
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                page_paragraphs = []
                current_para = []
                
                # Simple line grouping to identify paragraphs and distinct section headers
                for line in lines:
                    line_str = line.strip()
                    if not line_str:
                        if current_para:
                            page_paragraphs.append(" ".join(current_para))
                            current_para = []
                    # Check if line matches a header pattern (e.g., Section 1: ... or 2.1 ...)
                    elif line_str.startswith("Section ") or re.match(r'^\d+\.\d+\s+', line_str):
                        if current_para:
                            page_paragraphs.append(" ".join(current_para))
                            current_para = []
                        page_paragraphs.append(line_str)
                    else:
                        current_para.append(line_str)
                if current_para:
                    page_paragraphs.append(" ".join(current_para))
                
                for para in page_paragraphs:
                    # Update active section if this paragraph is a header
                    if para.startswith("Section ") or re.match(r'^\d+\.\d+\s+', para):
                        current_section = para
                        # Also add the header itself as a sentence so it is indexable
                        sentences_with_meta.append({
                            "text": para,
                            "page": page_number,
                            "section": current_section
                        })
                    else:
                        # Split regular paragraph into sentences
                        para_sentences = split_into_sentences(para)
                        for sent in para_sentences:
                            sentences_with_meta.append({
                                "text": sent,
                                "page": page_number,
                                "section": current_section
                            })
                            
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        raise e
        
    return sentences_with_meta

def chunk_sentences(sentences_with_meta: List[Dict[str, Any]], filename: str, tokenizer) -> List[Dict[str, Any]]:
    """
    Groups sentences into chunks of maximum 500 tokens with 50 tokens overlap.
    Uses the provided tokenizer to calculate exact token counts.
    """
    chunks = []
    current_chunk_sents = []
    current_chunk_tokens = 0
    
    def count_tokens(text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=False))

    def get_source_prefix(fname: str) -> str:
        # Convert e.g., "HR_Policy.pdf" to "hr_policy"
        base = os.path.splitext(fname)[0]
        return re.sub(r'[^a-z0-9_]', '', base.lower().replace('-', '_'))

    source_prefix = get_source_prefix(filename)
    
    i = 0
    while i < len(sentences_with_meta):
        sent = sentences_with_meta[i]
        sent_tokens = count_tokens(sent["text"])
        
        # Guard against single sentence exceeding the total chunk size
        if sent_tokens > 500:
            if current_chunk_sents:
                chunks.append(current_chunk_sents)
                current_chunk_sents = []
                current_chunk_tokens = 0
            chunks.append([sent])
            i += 1
            continue
            
        if current_chunk_tokens + sent_tokens > 500:
            chunks.append(current_chunk_sents)
            
            # Find the overlap window (approx 50 tokens from the tail of the chunk)
            overlap_sents = []
            overlap_tokens = 0
            for osent in reversed(current_chunk_sents):
                otok = count_tokens(osent["text"])
                if overlap_tokens + otok <= 50 or not overlap_sents:
                    overlap_sents.insert(0, osent)
                    overlap_tokens += otok
                else:
                    break
            
            current_chunk_sents = overlap_sents
            current_chunk_tokens = overlap_tokens
            
        current_chunk_sents.append(sent)
        current_chunk_tokens += sent_tokens
        i += 1
        
    if current_chunk_sents:
        chunks.append(current_chunk_sents)
        
    # Format chunks with unique IDs and structured metadata
    formatted_chunks = []
    for idx, chunk_sents in enumerate(chunks):
        combined_text = " ".join([s["text"] for s in chunk_sents])
        # Use page and section of the first sentence in the chunk as the primary metadata
        primary_page = chunk_sents[0]["page"]
        primary_section = chunk_sents[0]["section"]
        
        formatted_chunks.append({
            "text": combined_text,
            "metadata": {
                "source": filename,
                "page": primary_page,
                "chunk_id": f"{source_prefix}_chunk_{idx + 1}",
                "section": primary_section
            }
        })
        
    return formatted_chunks

def ingest_directory(docs_dir: str, tokenizer) -> List[Dict[str, Any]]:
    """Scans documents directory, processes all PDFs, and returns list of formatted chunks."""
    all_chunks = []
    if not os.path.exists(docs_dir):
        logger.warning(f"Documents directory {docs_dir} does not exist.")
        return []
        
    for file in os.listdir(docs_dir):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(docs_dir, file)
            logger.info(f"Ingesting: {pdf_path}")
            try:
                sentences = extract_sentences_from_pdf(pdf_path)
                chunks = chunk_sentences(sentences, file, tokenizer)
                all_chunks.extend(chunks)
                logger.info(f"Extracted {len(chunks)} chunks from {file}")
            except Exception as e:
                logger.error(f"Failed to ingest {file}: {e}")
                
    return all_chunks
