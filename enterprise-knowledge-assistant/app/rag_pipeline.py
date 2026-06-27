import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

from app.embeddings import get_embedding_model
from app.ingestion import ingest_directory
from app.retriever import HybridRetriever
from app.query_rewriter import QueryRewriter
from app.llm import LLMAnswerGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "./data/documents")

class RAGPipeline:
    _instance = None

    def __new__(cls):
        """Singleton pattern for RAG Pipeline initialization."""
        if cls._instance is None:
            cls._instance = super(RAGPipeline, cls).__new__(cls)
            logger.info("Initializing Meridian RAG Pipeline components...")
            cls._instance.embeddings = get_embedding_model()
            cls._instance.retriever = HybridRetriever(cls._instance.embeddings)
            cls._instance.rewriter = QueryRewriter()
            cls._instance.generator = LLMAnswerGenerator()
            logger.info("Meridian RAG Pipeline components initialized successfully.")
        return cls._instance

    def ask(self, question: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes the full RAG pipeline:
        1. Query rewriting (resolves history pronouns/context)
        2. Hybrid retrieval (semantic + lexical BM25)
        3. LLM Answer generation with metadata citation
        """
        if not question.strip():
            return {
                "answer": "Please ask a valid question.",
                "sources": [],
                "confidence": 0.0,
                "confidence_label": "Low",
                "rewritten_query": ""
            }

        try:
            # 1. Rewrite Query
            rewritten_query = self.rewriter.rewrite_query(question, history)
            
            # 2. Hybrid Retrieve
            retrieved_chunks = self.retriever.retrieve(rewritten_query)
            
            # If no chunks retrieved, return early
            if not retrieved_chunks:
                return {
                    "answer": "I could not find this information in the knowledge base.",
                    "sources": [],
                    "confidence": 0.0,
                    "confidence_label": "Low",
                    "rewritten_query": rewritten_query
                }
                
            # 3. Generate Answer
            answer, confidence, label = self.generator.generate_answer(question, retrieved_chunks)
            
            # Format source citations
            # If confidence is Low (e.g. answer not found), we don't display sources as relevant
            sources = []
            if label != "Low":
                for chunk in retrieved_chunks:
                    sources.append({
                        "document": chunk["metadata"]["source"],
                        "page": int(chunk["metadata"]["page"]),
                        "section": chunk["metadata"]["section"],
                        "text": chunk["text"]
                    })
                    
            return {
                "answer": answer,
                "sources": sources,
                "confidence": float(confidence),
                "confidence_label": label,
                "rewritten_query": rewritten_query
            }
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return {
                "answer": f"An error occurred in the RAG pipeline processing: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "confidence_label": "Low",
                "rewritten_query": question
            }

    def ingest(self) -> int:
        """
        Triggers re-ingestion of the documents directory.
        Cleans existing vectors and re-indexes all PDFs.
        """
        logger.info("Starting document ingestion process...")
        try:
            # Clear existing index
            self.retriever.delete_all()
            
            # Parse directory
            tokenizer = self.embeddings.model.tokenizer
            chunks = ingest_directory(DOCUMENTS_DIR, tokenizer)
            
            if not chunks:
                logger.warning("No documents found in ingestion directory.")
                return 0
                
            # Add to retriever
            self.retriever.add_documents(chunks)
            logger.info(f"Ingested {len(chunks)} chunks into ChromaDB.")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            raise e

    def get_documents(self) -> Dict[str, int]:
        """Returns indexed documents list with their chunk counts."""
        return self.retriever.get_indexed_documents()
