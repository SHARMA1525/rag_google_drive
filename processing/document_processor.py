import os
import re
import pdfplumber
from typing import List, Dict, Any
from core.logging_config import setup_logging

logger = setup_logging()

class DocumentProcessor:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text(self, file_path: str) -> str:
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.pdf':
            return self._extract_from_pdf(file_path)
        elif extension == '.txt':
            return self._extract_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file extension: {extension}")
            return ""

    def _extract_from_pdf(self, file_path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {str(e)}")
        return self._clean_text(text)

    def _extract_from_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return self._clean_text(f.read())
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {str(e)}")
        return ""

    def _clean_text(self, text: str) -> str:
        text = text.encode("ascii", "ignore").decode()
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        words = text.split(' ')
        chunks = []
        
        words_per_chunk = int(self.chunk_size * 0.75)
        overlap_words = int(self.chunk_overlap * 0.75)
        
        if len(words) <= words_per_chunk:
            return [{"text": text, "metadata": {**metadata, "chunk_index": 0}}]

        for i in range(0, len(words), words_per_chunk - overlap_words):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = ' '.join(chunk_words)
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "metadata": {**metadata, "chunk_index": len(chunks)}
                })
            
            if i + words_per_chunk >= len(words):
                break
                
        return chunks
