import datetime
import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_services.setup import validate_user_and_build_service

# The scope required for full read/write access to the user's calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_NAME = 'calendar'
VERSION = 'v3'
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_TOKEN = os.path.join(_CURRENT_DIR, 'calendar_token.json') # Assuming this is how you pass your credentials

def read_calender():
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Get the current time in UTC format required by the API
    now = datetime.datetime.utcnow().isoformat() + 'Z' 
    print('Fetching the upcoming 10 events...')
    
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=now,
        maxResults=10, 
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    if not events:
        print('No upcoming events found.')
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            
    return events

def create_task_calender(summary, start_time, end_time, description="", event_id=None):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Construct the event body
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time, # Format: '2026-08-25T09:00:00-07:00'
            'timeZone': 'UTC',      # Adjust timezone as needed
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }

    try:
        request = service.events().insert(calendarId='primary', body=event_body)
        event = request.execute()
        return event
    except Exception as e:
        print(f"   ✗ Error creating calendar event: {e}")
        return None

def edit_task_calender(event_id, updated_summary=None, updated_description=None):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # 1. Retrieve the existing event
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    
    # 2. Modify the desired fields
    if updated_summary:
        event['summary'] = updated_summary
    if updated_description:
        event['description'] = updated_description
        
    # 3. Push the update to Google Calendar
    updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    print(f"Event updated: {updated_event.get('htmlLink')}")
    return updated_event

def delete_task_calender(event_id):
    service = validate_user_and_build_service(SERVICE_NAME, SERVICE_TOKEN, SCOPES, VERSION)
    
    # Delete the event by its unique ID
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    print(f"Event {event_id} deleted successfully.")


# create_task_calender(summary="No Summary?",start_time="2026-08-25T09:00:00-07:00",end_time="2026-08-25T09:00:00-08:00",description="no description")