import os
from connectors.google_drive import GoogleDriveConnector
from database.db import Database
from core.logging_config import setup_logging
from datetime import datetime

logger = setup_logging()

class SyncService:
    def __init__(self, db: Database, connector: GoogleDriveConnector):
        self.db = db
        self.connector = connector

    def sync(self):
        logger.info("Starting Google Drive sync...")
        files = self.connector.list_files()
        new_or_modified_files = []

        for file in files:
            file_id = file['id']
            file_name = file['name']
            modified_time = file['modifiedTime']
            mime_type = file['mimeType']

            existing_file = self.db.get_file(file_id)
            
            if not existing_file or existing_file['modified_time'] != modified_time:
                logger.info(f"Syncing file: {file_name} (ID: {file_id})")
                try:
                    local_path = self.connector.download_file(file_id, file_name, mime_type)
                    self.db.upsert_file(file_id, file_name, modified_time, local_path)
                    new_or_modified_files.append({
                        "file_id": file_id,
                        "file_name": file_name,
                        "local_path": local_path
                    })
                except Exception as e:
                    logger.error(f"Failed to sync file {file_name}: {str(e)}")

        logger.info(f"Sync completed. {len(new_or_modified_files)} files updated.")
        return new_or_modified_files
