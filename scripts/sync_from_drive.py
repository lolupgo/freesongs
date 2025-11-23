import io
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

FOLDER_ID = "1YaXYCdcLZ0WI1X_6klCLeoFP-eLrIXLi"

SERVICE_ACCOUNT_INFO = json.loads(os.environ["GDRIVE_SERVICE_ACCOUNT_JSON"])
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def list_audio_files(service):
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='audio/mpeg' and trashed=false",
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])

def download_file(service, file_id, name):
    request = service.files().get_media(fileId=file_id)
    filepath = os.path.join("songs", name)
    os.makedirs("songs", exist_ok=True)

    fh = io.FileIO(filepath, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

def main():
    service = get_drive_service()
    files = list_audio_files(service)

    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")

    base_url = f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/songs/"

    songs = []

    for f in files:
        print("Downloading:", f["name"])
        download_file(service, f["id"], f["name"])

        songs.append({
            "name": f["name"],
            "url": base_url + f["name"]
        })

    with open("songs.json", "w") as fp:
        json.dump(songs, fp, indent=2)

if __name__ == "__main__":
    main()
