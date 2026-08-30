import io
from typing import Optional
import os
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from google_services.setup import validate_user_and_build_service

# The scope required for full read/write/delete access to Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_NAME = 'drive'
VERSION = 'v3'
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_TOKEN = os.path.join(_CURRENT_DIR, 'drive_token.json')

def read_drive(query: Optional[str] = None):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)

    items = []
    page_token = None
    while True:
        results = service.files().list(
            q=query or 'trashed = false',
            pageSize=1000,
            pageToken=page_token,
            corpora='user',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            orderBy='name_natural',
            fields=(
                'nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, '
                'size, md5Checksum, webViewLink, owners(displayName,emailAddress), '
                'parents, trashed)'
            ),
        ).execute()
        items.extend(results.get('files', []))
        page_token = results.get('nextPageToken')
        if not page_token:
            break

    if not items:
        print('No files found.')

    files_by_id = {item['id']: item for item in items}

    def parent_path(file_id, seen=None):
        seen = seen or set()
        if file_id in seen:
            return ''
        seen.add(file_id)
        item = files_by_id.get(file_id, {})
        parent_id = (item.get('parents') or [None])[0]
        if not parent_id:
            return ''
        parent = files_by_id.get(parent_id)
        if parent is None:
            return ''
        ancestor_path = parent_path(parent_id, seen)
        return f"{ancestor_path}/{parent['name']}" if ancestor_path else f"/{parent['name']}"

    for item in items:
        item['parent_ids'] = item.get('parents', [])
        parent_id = (item.get('parents') or [None])[0]
        parent = files_by_id.get(parent_id, {})
        item['parent_name'] = parent.get('name', '')
        item['parent_path'] = parent_path(item['id'])
        item['owner_names'] = [owner.get('displayName', '') for owner in item.get('owners', [])]
        item['owner_emails'] = [owner.get('emailAddress', '') for owner in item.get('owners', [])]
        print(f"{item['name']} ({item['id']}) - {item['mimeType']} {item['parent_path']}")

    return items

def create_drive_file(file_path, file_name, mime_type, parent_id=None):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Metadata contains the name the file will have in Google Drive
    file_metadata = {'name': file_name}
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    # Media body contains the actual file from your local system
    media = MediaFileUpload(file_path, mimetype=mime_type)
    
    try:
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, name, webViewLink, mimeType'
        ).execute()
        
        return file
    except Exception as e:
        print(f"   ✗ Error uploading file {file_name}: {e}")
        return None


def create_drive_folder(folder_name, parent_id=None):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    try:
        folder = service.files().create(body=file_metadata, fields='id, name, webViewLink').execute()
        return folder
    except Exception as e:
        print(f"   ✗ Error creating folder {folder_name}: {e}")
        return {}

def edit_drive_file(file_id, new_name):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # For Google Drive, "editing" usually means updating metadata (like the file name)
    # or updating the file content. Here, we update the file's name.
    file_metadata = {'name': new_name}
    
    updated_file = service.files().update(
        fileId=file_id, 
        body=file_metadata, 
        fields='id, name'
    ).execute()
    
    print(f"File updated. New name: {updated_file.get('name')}")
    return updated_file

def delete_drive_file(file_id):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # This permanently deletes the file. 
    # If you just want to move it to the trash, you would use edit_drive_file 
    # and pass {'trashed': True} in the file_metadata.
    service.files().delete(fileId=file_id).execute()
    
    print(f"File {file_id} deleted successfully.")

def download_drive_file(file_id, output_path):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Request the file media content
    request = service.files().get_media(fileId=file_id)
    
    # Open a local file stream to write the downloaded bytes
    fh = io.FileIO(output_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    print(f"Starting download for file ID: {file_id}...")
    
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download progress: {int(status.progress() * 100)}%")
        
    print(f"File successfully downloaded and saved to: {output_path}")