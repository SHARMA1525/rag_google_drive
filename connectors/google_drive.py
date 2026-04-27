import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from core.logging_config import setup_logging

logger = setup_logging()

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DEFAULT_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

class GoogleDriveConnector:
    def __init__(self, credentials_path: str = None, token_path: str = 'token.json'):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = token_path
        self.service = None
        
        creds = self._load_creds()
        if creds:
            self.service = build('drive', 'v3', credentials=creds)

    def _load_creds(self):
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            if creds and creds.valid:
                return creds
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                return creds
        return None

    def get_auth_url(self, redirect_uri: str = DEFAULT_REDIRECT_URI):
        flow = self._get_flow(redirect_uri)
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        return auth_url

    def fetch_token(self, code: str, redirect_uri: str = DEFAULT_REDIRECT_URI):
        flow = self._get_flow(redirect_uri)
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open(self.token_path, 'w') as token:
            token.write(creds.to_json())
        self.service = build('drive', 'v3', credentials=creds)
        return True

    def _get_flow(self, redirect_uri: str):
        if os.path.exists(self.credentials_path):
            flow = Flow.from_client_secrets_file(self.credentials_path, scopes=SCOPES, redirect_uri=redirect_uri)
        else:
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            if not client_id or not client_secret:
                raise ValueError("Neither credentials.json nor GOOGLE_CLIENT_ID/SECRET env vars found.")
            
            client_config = {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)
        return flow

    def is_authenticated(self):
        return self.service is not None

    def list_files(self, query: str = "mimeType='application/pdf' or mimeType='application/vnd.google-apps.document' or mimeType='text/plain'"):
        results = self.service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, modifiedTime, mimeType)"
        ).execute()
        return results.get('files', [])

    def download_file(self, file_id: str, file_name: str, mime_type: str, download_dir: str = "data/downloads"):
        os.makedirs(download_dir, exist_ok=True)
        
        if mime_type == 'application/vnd.google-apps.document':
            request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
            file_extension = '.txt'
        else:
            request = self.service.files().get_media(fileId=file_id)
            file_extension = os.path.splitext(file_name)[1]

        file_path = os.path.join(download_dir, f"{file_id}{file_extension}")
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                logger.info(f"Download {file_name} progress: {int(status.progress() * 100)}%")

        with open(file_path, 'wb') as f:
            f.write(fh.getvalue())
        
        return file_path
