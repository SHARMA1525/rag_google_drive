import os
from connectors.sync_service import SyncService
from processing.document_processor import DocumentProcessor
from embedding.embedder import Embedder
from search.vector_store import VectorStore
from llm.client import get_llm_provider
from database.db import Database
from cache.query_cache import QueryCache
from core.logging_config import setup_logging
from typing import List, Dict, Any

logger = setup_logging()

class RAGService:
    def __init__(self):
        self.db = Database()
        self.processor = DocumentProcessor()
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.cache = QueryCache()
        self.llm = get_llm_provider()

    def sync_drive(self):
        from connectors.google_drive import GoogleDriveConnector
        connector = GoogleDriveConnector()
        
        if not connector.is_authenticated():
            raise ValueError("Google Drive not authenticated. Please login first.")
            
        sync_service = SyncService(self.db, connector)
        
        updated_files = sync_service.sync()
        
        for i, file in enumerate(updated_files):
            logger.info(f"Processing file {i+1}/{len(updated_files)}: {file['file_name']}")
            text = self.processor.extract_text(file['local_path'])
            if text:
                metadata = {
                    "file_id": file['file_id'],
                    "file_name": file['file_name'],
                    "source": "gdrive"
                }
                chunks = self.processor.chunk_text(text, metadata)
                texts = [c['text'] for c in chunks]
                logger.info(f"Generating embeddings for {len(texts)} chunks from {file['file_name']}")
                embeddings = self.embedder.embed_texts(texts)
                self.vector_store.add_embeddings(embeddings, chunks)
        
        return {"status": "success", "updated_files": [f['file_name'] for f in updated_files]}

    def process_file(self, file_path: str, file_name: str):
        """Helper to process a local file and add it to the vector store."""
        text = self.processor.extract_text(file_path)
        if text:
            metadata = {
                "file_id": file_name, 
                "file_name": file_name,
                "source": "manual_upload"
            }
            chunks = self.processor.chunk_text(text, metadata)
            texts = [c['text'] for c in chunks]
            embeddings = self.embedder.embed_texts(texts)
            self.vector_store.add_embeddings(embeddings, chunks)
            
            from datetime import datetime
            self.db.upsert_file(file_name, file_name, datetime.now().isoformat(), file_path)
            return True
        return False

    def get_auth_url(self):
        from connectors.google_drive import GoogleDriveConnector
        connector = GoogleDriveConnector()
        return connector.get_auth_url()

    def complete_auth(self, code: str):
        from connectors.google_drive import GoogleDriveConnector
        connector = GoogleDriveConnector()
        return connector.fetch_token(code)

    def is_authenticated(self):
        from connectors.google_drive import GoogleDriveConnector
        connector = GoogleDriveConnector()
        return connector.is_authenticated()

    def logout(self):
        token_path = 'token.json'
        if os.path.exists(token_path):
            os.remove(token_path)
        logger.info("User logged out, token.json removed")
        return True

    def ask(self, query: str):
        cached_response = self.cache.get(query)
        if cached_response:
            return cached_response

        query_embedding = self.embedder.embed_query(query)
        relevant_chunks = self.vector_store.search(query_embedding)
        
        if not relevant_chunks:
            return {"answer": "There is no file found containing information on this topic.", "sources": []}

        context = "\n\n".join([c['text'] for c in relevant_chunks])
        sources = list(set([c['metadata']['file_name'] for c in relevant_chunks]))
        
        try:
            answer = self.llm.generate_answer(query, context)
        except Exception as e:
            logger.error(f"LLM Generation failed: {str(e)}")
            raise e
        
        response = {
            "answer": answer,
            "sources": sources
        }
        
        self.cache.set(query, response)
        self.db.log_query(query, answer, sources)
        
        return response

    def get_health(self):
        return {"status": "healthy", "files_synced": len(self.db.list_files())}
