import base64
from email.message import EmailMessage
from google_services.setup import validate_user_and_build_service
import os

# The scope required for full read/write/delete access to Gmail
SCOPES = ['https://mail.google.com/']
SERVICE_NAME = 'gmail'
VERSION = 'v1'
SERVICE_TOKEN = 'gmail_token.json' 


def has_attachments(payload):
    """
    Recursively checks if any part of the email payload contains an attachment.
    """
    # Check if the current payload part has a filename and an attachment ID
    filename = payload.get('filename')
    body = payload.get('body', {})
    if filename and body.get('attachmentId'):
        return True
        
    # If it's multipart, check all sub-parts recursively
    if 'parts' in payload:
        for part in payload['parts']:
            if has_attachments(part):
                return True
                
    return False


def get_email_body(payload):
    """
    Extracts the plain text body from the email payload.
    """
    # Base case: the email is not multipart, the body is right in the payload
    if 'data' in payload.get('body', {}):
        data = payload['body']['data']
        # Decode the Base64 URL-encoded string
        return base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8')
    
    # If the email is multipart, we need to dig into the 'parts' array
    if 'parts' in payload:
        for part in payload['parts']:
            # Look for the plain text version of the email
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data')
                if data:
                    return base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8')
            
            # Sometimes parts have sub-parts (like an inline image inside an HTML body)
            # You can recursively call this function to dig deeper if needed
            elif 'parts' in part:
                return get_email_body(part)
                
    return "No plain text body found."


def read_gmail() -> list[dict]:
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    print('Fetching the latest 5 emails...')
    # userId='me' is a special value indicating the authenticated user
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])

    messages_list = []
    if not messages:
        print('No messages found.')
    else:
        for msg in messages:
            # You have to do a second API call to get the actual content/headers of each message
            msg_data = service.users().messages().get(
                userId='me', id=msg['id'], format='full'
            ).execute()
            
            headers = msg_data.get('payload', {}).get('headers', [])
            
            email_title = next(
                (header['value'] for header in headers
                 if header.get('name', '').lower() == 'subject'),
                'No Subject'
            )
            email_date = next(
                (header['value'] for header in headers
                 if header.get('name', '').lower() == 'date'),
                'Unknown Date'
            )
            
            payload = msg_data.get('payload', {})   
            email_has_attachment = has_attachments(payload)
            email_body = get_email_body(payload)
            
            # --- NEW LOGIC: Extract Attachment IDs and Filenames ---
            attachment_ids = []
            attachment_filenames = []
            
            def extract_attachments(part):
                filename = part.get('filename')
                attachment_id = part.get('body', {}).get('attachmentId')
                
                # If both exist, this part is an attachment
                if filename and attachment_id:
                    attachment_filenames.append(filename)
                    attachment_ids.append(attachment_id)
                    
                # Recursively check nested parts (common in multipart emails)
                if 'parts' in part:
                    for subpart in part['parts']:
                        extract_attachments(subpart)
            
            # Run the extraction on the main payload
            extract_attachments(payload)
            # -------------------------------------------------------
            
            print(f"Message Snippet: {msg_data.get('snippet')}")
            messages_list.append({
                "id": msg["id"],
                "email_title": email_title,
                "email_date": email_date,
                "email_snippet": msg_data.get('snippet'),
                "has_attachment": email_has_attachment,
                "email_body": email_body,
                "attachment_ids": attachment_ids,                 # Added to dict
                "attachment_filenames": attachment_filenames      # Added to dict
            })
            
    return messages_list




def download_attachment(message_id, attachment_id, file_name, save_folder="attachments"):
    """
    Downloads and decodes an attachment from a Gmail message using the attachment ID.
    """
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    try:
        # Request the specific attachment data from the API
        attachment = service.users().messages().attachments().get(
            userId='me', 
            messageId=message_id, 
            id=attachment_id
        ).execute()

        # The data is returned as a Base64 URL-encoded string
        data = attachment.get('data')
        if not data:
            return None
            
        # Decode the string back into raw file bytes
        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))

        # Ensure the destination folder exists, then write the file
        os.makedirs(save_folder, exist_ok=True)
        file_path = os.path.join(save_folder, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
            
        return file_path
        
    except Exception as e:
        print(f"An error occurred downloading attachment {file_name}: {e}")
        return None


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


# emails = read_gmail()
# print("type of emails",type(emails))
# print("emails are",emails)