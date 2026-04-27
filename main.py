import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os
from dotenv import load_dotenv
from api.rag_service import RAGService
from core.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

app = FastAPI(title="DriveRAG API", version="1.0.0")
rag_service = RAGService()

@app.get("/")
async def root():
    return {
        "message": "DriveRAG API is running!",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "sync_drive": "/sync-drive",
            "upload": "/upload",
            "auth_url": "/auth/url",
            "auth_status": "/auth/status",
            "auth_callback": "/auth/callback"
        }
    }

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

class SyncResponse(BaseModel):
    status: str
    updated_files: List[str]

@app.post("/sync-drive", response_model=SyncResponse)
async def sync_drive():
    try:
        logger.info("Received request to sync Google Drive")
        result = rag_service.sync_drive()
        return result
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Manual upload endpoint removed as per new requirements.

@app.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    try:
        logger.info(f"Received query: {request.query}")
        result = rag_service.ask(request.query)
        return result
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return rag_service.get_health()

@app.get("/auth/url")
async def get_auth_url():
    try:
        return {"url": rag_service.get_auth_url()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/callback")
async def auth_callback(code: str):
    try:
        rag_service.complete_auth(code)
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content="""
            <html>
                <body style="font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5;">
                    <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
                        <h1 style="color: #4F46E5;">Authentication Successful!</h1>
                        <p>You have successfully connected Google Drive. You can now close this window and return to the assistant.</p>
                        <a href="http://localhost:8501" style="display: inline-block; margin-top: 1rem; padding: 0.5rem 1rem; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 4px;">Return to App</a>
                    </div>
                </body>
            </html>
        """)
    except Exception as e:
        logger.error(f"Auth callback failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/status")
async def auth_status():
    return {"authenticated": rag_service.is_authenticated()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
