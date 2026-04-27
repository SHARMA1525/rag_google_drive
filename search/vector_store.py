import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Tuple
from core.logging_config import setup_logging

logger = setup_logging()

class VectorStore:
    def __init__(self, dimension: int = 384, index_path: str = "data/vectorstore"):
        self.dimension = dimension
        self.index_path = index_path
        self.faiss_index_file = os.path.join(index_path, "index.faiss")
        self.metadata_file = os.path.join(index_path, "metadata.pkl")
        
        os.makedirs(index_path, exist_ok=True)
        
        if os.path.exists(self.faiss_index_file):
            self.index = faiss.read_index(self.faiss_index_file)
            with open(self.metadata_file, 'rb') as f:
                self.chunks = pickle.load(f)
            logger.info(f"Loaded existing index with {len(self.chunks)} chunks")
        else:
            self.index = faiss.IndexFlatIP(dimension)
            self.chunks = []
            logger.info("Created new FAISS index")

    def add_embeddings(self, embeddings: np.ndarray, chunks: List[Dict[str, Any]]):
        if len(embeddings) == 0:
            return
        
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        self.save()
        logger.info(f"Added {len(chunks)} chunks to index")

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []
        
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk['score'] = float(distances[0][i])
                results.append(chunk)
        
        return results

    def save(self):
        faiss.write_index(self.index, self.faiss_index_file)
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.chunks, f)
        logger.info("Saved FAISS index and metadata")

    def clear(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []
        if os.path.exists(self.faiss_index_file):
            os.remove(self.faiss_index_file)
        if os.path.exists(self.metadata_file):
            os.remove(self.metadata_file)
        logger.info("Cleared vector store")
