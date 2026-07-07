import os
import json
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    token_file = "token.json"
    if not os.path.exists(token_file):
        print(f"No token.json found in {os.getcwd()}")
        return

    scopes = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_authorized_user_file(token_file, scopes)
    service = build("drive", "v3", credentials=creds)

    print("Buscando planillas de cálculo (spreadsheets) en Google Drive...")
    query = "mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
    
    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, parents)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        pageSize=50
    ).execute()

    files = results.get("files", [])
    if not files:
        print("No se encontraron planillas.")
    else:
        print(f"Se encontraron {len(files)} planillas:")
        for f in files:
            name = f.get('name', '')
            safe_name = name.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            print(f"ID: {f.get('id')} | Nombre: {safe_name} | Parents: {f.get('parents')}")

if __name__ == '__main__':
    main()
