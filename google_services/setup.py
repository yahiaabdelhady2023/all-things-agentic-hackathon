import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION):
    creds = None
    # token.json stores the user's access and refresh tokens. It is created automatically
    # when the authorization flow completes for the first time.
    if os.path.exists(SERVICE_TOKEN):
        creds = Credentials.from_authorized_user_file(SERVICE_TOKEN, SCOPES)
        
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run so you don't have to log in every time
        with open(SERVICE_TOKEN, 'w') as token:
            token.write(creds.to_json())
    try:
        service = build(SERVICE_NAME, VERSION, credentials=creds)
        return service
    except Exception as e:
        print(f"error occurred while trying to build {SERVICE_NAME} error is {e}")
