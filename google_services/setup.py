import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError


def validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION):
    creds = None
    # token.json stores the user's access and refresh tokens. It is created automatically
    # when the authorization flow completes for the first time.
    if os.path.exists(SERVICE_TOKEN):
        try:
            creds = Credentials.from_authorized_user_file(SERVICE_TOKEN, SCOPES)
        except Exception as e:
            print(f"⚠ Could not load credentials for {SERVICE_NAME}: {e}")
            creds = None
        
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                print(f"🔄 Refreshing expired credentials for {SERVICE_NAME}...")
                try:
                    creds.refresh(Request())
                except RefreshError as refresh_err:
                    print(f"❌ Token refresh failed: {refresh_err}")
                    print(f"   Deleting expired token: {SERVICE_TOKEN}")
                    if os.path.exists(SERVICE_TOKEN):
                        os.remove(SERVICE_TOKEN)
                    creds = None
            
            if not creds:
                print(f"🔐 Re-authenticating {SERVICE_NAME}...")
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "credentials.json not found! Please download it from Google Cloud Console:\n"
                        "1. Go to Google Cloud Console\n"
                        "2. Create OAuth 2.0 credentials (Desktop app)\n"
                        "3. Download and save as 'credentials.json'"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
        except Exception as e:
            print(f"❌ Authentication failed for {SERVICE_NAME}: {e}")
            raise
            
        # Save the credentials for the next run so you don't have to log in every time
        try:
            with open(SERVICE_TOKEN, 'w') as token:
                token.write(creds.to_json())
            print(f"✓ Credentials saved for {SERVICE_NAME}")
        except Exception as e:
            print(f"⚠ Could not save credentials: {e}")
            
    try:
        service = build(SERVICE_NAME, VERSION, credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Error building {SERVICE_NAME} service: {e}")
        raise
