import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
RUTA_CREDENCIALES = "data/credentials.json"
RUTA_TOKEN = "data/token.json"

def obtener_credenciales():
    creds = None
    if os.path.exists(RUTA_TOKEN):
        creds = Credentials.from_authorized_user_file(RUTA_TOKEN, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            if not os.path.exists(RUTA_CREDENCIALES):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(RUTA_CREDENCIALES, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(RUTA_TOKEN, 'w') as token:
            token.write(creds.to_json())
    return creds

def subir_a_drive_real(ruta_archivo, nombre_archivo, id_carpeta):
    creds = obtener_credenciales()
    if not creds:
        return False
        
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {
            'name': nombre_archivo,
            'parents': [id_carpeta]
        }
        media = MediaFileUpload(ruta_archivo, mimetype='application/pdf')
        
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return True
    except Exception:
        return False