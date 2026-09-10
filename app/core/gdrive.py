import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


class GDriveClient:
    def __init__(self):
        self.service = None
        self._authenticated = False

    def authenticate(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"No se encontro {CREDENTIALS_FILE}. "
                        "Descargalo de Google Cloud Console > APIs & Services > Credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=8080)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        self.service = build("drive", "v3", credentials=creds)
        self._authenticated = True
        logger.info("Autenticacion con Google Drive exitosa.")

    @property
    def is_authenticated(self):
        return self._authenticated

    def upload_file(self, file_path, folder_id=None, name_prefix=""):
        if not self._authenticated:
            raise RuntimeError("No autenticado con Google Drive.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        file_name = os.path.basename(file_path)
        file_metadata = {"name": file_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        file_size = os.path.getsize(file_path)

        result = self.service.files().create(
            body=file_metadata, media_body=media, fields="id,name,size"
        ).execute()

        logger.info(f"Archivo subido: {result.get('name')} (ID: {result.get('id')})")
        return result

    def list_folders(self, page_size=100):
        if not self._authenticated:
            raise RuntimeError("No autenticado con Google Drive.")

        results = self.service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=page_size,
            fields="nextPageToken, files(id, name)",
        ).execute()
        return results.get("files", [])
