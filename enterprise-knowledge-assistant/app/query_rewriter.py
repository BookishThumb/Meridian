import os
import time
import logging
from typing import List, Dict, Any
from groq import Groq
import groq
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "openai/gpt-oss-20b")

class QueryRewriter:
    def __init__(self):
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY environment variable is not set. Query rewriter will fail.")
        self.client = Groq(api_key=GROQ_API_KEY)

    def rewrite_query(self, question: str, history: List[Dict[str, str]] = None) -> str:
        """
        Rewrites a user's question to be standalone and search-friendly.
        If history is provided (list of dicts with keys 'role' and 'content'),
        it resolves pronouns, context, and follow-ups.
        """
        if not GROQ_API_KEY:
            logger.warning("Groq API key missing. Returning original query.")
            return question

        if not question.strip():
            return ""

        # Format history if it exists
        history_str = ""
        if history:
            for turn in history[-5:]:  # Limit to last 5 turns
                role = "User" if turn["role"] == "user" else "Assistant"
                history_str += f"{role}: {turn['content']}\n"

        system_prompt = (
            "You are an expert query rewriting assistant. Given a conversation history and a follow-up question, "
            "your job is to rewrite the follow-up question to be a standalone, keyword-rich search query "
            "designed for a search engine or vector database.\n\n"
            "Rules:\n"
            "1. Resolve any pronoun references (like 'it', 'they', 'them', 'this') to their concrete subjects based on history.\n"
            "2. Strip out conversational filler (e.g. 'tell me about', 'could you search for', 'please explain').\n"
            "3. Focus on primary search terms (nouns, verbs, specific entities).\n"
            "4. Output ONLY the final search query. Do NOT add any notes, explanation, quotes, or conversational prefix.\n\n"
            "Example:\n"
            "History:\n"
            "User: How many paid leaves do we get?\n"
            "Assistant: Employees get 24 paid leaves per year.\n"
            "Follow-up: and what about sick ones?\n"
            "Output: sick leave policy number of days"
        )

        user_content = f"History:\n{history_str if history_str else 'No history.'}\nFollow-up: {question}\nOutput:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        logger.info(f"Invoking Groq rewriter '{GROQ_FAST_MODEL}'...")
        
        max_retries = 3
        backoff = 2.0
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=GROQ_FAST_MODEL,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=100
                )
                raw_rewritten = response.choices[0].message.content
                logger.info(f"Raw rewriter output for '{question}': '{raw_rewritten}'")
                rewritten = raw_rewritten.strip()
                # Clean up any quotes the model might have returned
                rewritten = rewritten.strip('"\'')
                if not rewritten.strip():
                    logger.warning("Query rewriter returned empty string. Falling back to original question.")
                    rewritten = question
                logger.info(f"Original: '{question}' -> Rewritten: '{rewritten}'")
                return rewritten
            except groq.RateLimitError as e:
                if attempt == max_retries:
                    logger.error("Rate limit retries exhausted for Query Rewriter. Returning original query.")
                    return question
                
                sleep_time = backoff ** attempt
                logger.warning(f"Groq API Rate Limit hit. Retrying rewriter in {sleep_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Error in query rewriter: {e}. Returning original query.")
                return question
                
        return question
