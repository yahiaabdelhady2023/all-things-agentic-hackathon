import base64
from email.message import EmailMessage
from __setup import validate_user_and_build_service
import base64

# The scope required for full read/write/delete access to Gmail
SCOPES = ['https://mail.google.com/']
SERVICE_NAME = 'gmail'
VERSION = 'v1'
SERVICE_TOKEN = 'gmail_token.json' 

def read_gmail():
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    print('Fetching the latest 5 emails...')
    # userId='me' is a special value indicating the authenticated user
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        for msg in messages:
            # You have to do a second API call to get the actual content/headers of each message
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            print(f"Message Snippet: {msg_data.get('snippet')}")
            
    return messages



def read_specific_email(message_id):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    print(f"Fetching email with ID: {message_id}...")
    
    # Request the full format of the specific message
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    
    payload = message.get('payload', {})
    headers = payload.get('headers', [])
    
    # Extract specific headers by searching through the headers list
    subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
    sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')
    date = next((header['value'] for header in headers if header['name'].lower() == 'date'), 'Unknown Date')
    
    print("-" * 30)
    print(f"Date: {date}")
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print("-" * 30)
    
    # The snippet provides a quick preview of the email body (up to ~200 characters)
    print(f"Snippet: {message.get('snippet')}")
    print("-" * 30)
    
    return message


def create_gmail_draft(to_email, subject, body_text):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Construct the MIME message
    message = EmailMessage()
    message.set_content(body_text)
    message['To'] = to_email
    message['Subject'] = subject

    # Gmail API requires the message to be base64url encoded
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {'message': {'raw': encoded_message}}

    draft = service.users().drafts().create(userId='me', body=create_message).execute()
    print(f"Draft created with ID: {draft['id']}")
    return draft

def edit_gmail_draft(draft_id, to_email, subject, body_text):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Reconstruct the updated MIME message
    message = EmailMessage()
    message.set_content(body_text)
    message['To'] = to_email
    message['Subject'] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    update_draft = {'message': {'raw': encoded_message}}

    # Update the existing draft
    draft = service.users().drafts().update(userId='me', id=draft_id, body=update_draft).execute()
    print(f"Draft {draft_id} updated successfully.")
    return draft

def delete_gmail_message(message_id):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Using .trash() moves it to the bin. 
    # If you want permanent deletion, use .delete() instead.
    service.users().messages().trash(userId='me', id=message_id).execute()
    print(f"Message {message_id} moved to trash.")


read_gmail()