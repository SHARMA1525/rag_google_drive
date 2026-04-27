from processing.document_processor import DocumentProcessor
import os

dp = DocumentProcessor()
pdf_path = "data/downloads/ai_basics.pdf"

if os.path.exists(pdf_path):
    text = dp.extract_text(pdf_path)
    print(f"--- EXTRACTED TEXT (First 500 chars) ---\n{text[:500]}...")
else:
    print(f"File not found: {pdf_path}")
