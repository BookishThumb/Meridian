import os
import time
import logging
from typing import List, Dict, Any, Tuple
from groq import Groq
import groq
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_PRIMARY_MODEL = os.getenv("GROQ_PRIMARY_MODEL", "llama-3.3-70b-versatile")

class LLMAnswerGenerator:
    def __init__(self):
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY environment variable is not set. LLM queries will fail.")
        # Initialize Groq client
        self.client = Groq(api_key=GROQ_API_KEY)

    def generate_answer(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[str, float, str]:
        """
        Generates an answer using llama-3.3-70b-versatile based on the context.
        Returns: Tuple[answer_text, confidence_score, confidence_label]
        """
        if not GROQ_API_KEY:
            return "Error: GROQ_API_KEY is not configured.", 0.0, "Low"

        # Determine confidence score based on the highest retrieval combined score
        best_combined = retrieved_chunks[0]["combined_score"] if retrieved_chunks else 0.0
        
        # Guardrail: Low combined score (< 0.35) automatically triggers "information not found"
        # to avoid hallucinations and save API costs.
        if best_combined < 0.35:
            logger.info(f"Top combined score ({best_combined:.4f}) is below 0.35 threshold. Returning default 'not found' response.")
            return "I could not find this information in the knowledge base.", best_combined, "Low"

        # Classify confidence label based on combined score threshold
        if best_combined >= 0.50:
            confidence_label = "High"
        else:
            confidence_label = "Medium"

        # Format context for system prompt
        context_str = ""
        for chunk in retrieved_chunks:
            source = chunk["metadata"]["source"]
            page = chunk["metadata"]["page"]
            section = chunk["metadata"]["section"]
            text = chunk["text"]
            context_str += f"[Document: {source}, Page: {page}, Section: {section}]\nText: {text}\n\n"

        system_prompt = (
            "You are an enterprise knowledge assistant for AnthraSync Technologies.\n"
            "Answer questions strictly based on the provided context.\n"
            "If the answer is not in the context, say \n"
            "'I could not find this information in the knowledge base.'\n"
            "Never make up information. Always mention the source document (e.g. HR_Policy.pdf) and section in your answer."
        )

        user_content = f"Context:\n{context_str}\nQuestion: {question}\n\nAnswer:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        logger.info(f"Invoking Groq model '{GROQ_PRIMARY_MODEL}' with {len(retrieved_chunks)} context chunks...")
        
        # Call Groq with exponential backoff retry logic
        answer = ""
        max_retries = 3
        backoff = 2.0
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=GROQ_PRIMARY_MODEL,
                    messages=messages,
                    temperature=0.0,  # Deterministic factual answers
                    max_tokens=1024
                )
                answer = response.choices[0].message.content.strip()
                break
            except groq.RateLimitError as e:
                if attempt == max_retries:
                    logger.error("Rate limit retries exhausted. Operation failed.")
                    return "Error: Groq API Rate Limit reached. Please try again later.", best_combined, "Low"
                
                sleep_time = backoff ** attempt
                logger.warning(f"Groq API Rate Limit hit. Retrying in {sleep_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Error calling Groq API: {e}")
                return f"Error: An unexpected error occurred while communicating with the LLM API. {str(e)}", best_combined, "Low"

        # Check if the LLM returned its standard "not found" response
        not_found_phrases = [
            "could not find this information",
            "not found in the knowledge base",
            "not mentioned in the context",
            "information is not in the context"
        ]
        
        if any(phrase in answer.lower() for phrase in not_found_phrases):
            logger.info("LLM determined that the answer is not present in the retrieved context.")
            return "I could not find this information in the knowledge base.", best_combined, "Low"

        return answer, best_combined, confidence_label
