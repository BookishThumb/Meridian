import os
import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Get model name from environment or use default
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

class EmbeddingModel:
    _instance = None

    def __new__(cls):
        """Singleton pattern to avoid loading the model multiple times."""
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
            try:
                cls._instance.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise e
        return cls._instance

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        if not text.strip():
            return []
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document chunks in a batch."""
        if not texts:
            return []
        try:
            embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise e

# Convenience functions
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()
