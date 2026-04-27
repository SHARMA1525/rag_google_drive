from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from core.logging_config import setup_logging

logger = setup_logging()

class Embedder:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        logger.info(f"Generating embeddings for {len(texts)} chunks")
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        return self.model.encode([query], convert_to_numpy=True)[0]
