import io
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from google_services.setup import validate_user_and_build_service

# The scope required for full read/write/delete access to Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_NAME = 'drive'
VERSION = 'v3'
SERVICE_TOKEN = 'drive_token.json'

def read_drive():
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    print('Fetching the first 10 files...')
    # list() returns the files. We specify the fields we want to make the response lighter.
    results = service.files().list(
        pageSize=10, 
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        for item in items:
            print(f"{item['name']} ({item['id']}) - {item['mimeType']}")
            
    return items

def create_drive_file(file_path, file_name, mime_type):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Metadata contains the name the file will have in Google Drive
    file_metadata = {'name': file_name}
    
    # Media body contains the actual file from your local system
    media = MediaFileUpload(file_path, mimetype=mime_type)
    
    file = service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id'
    ).execute()
    
    print(f"File created with ID: {file.get('id')}")
    return file

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