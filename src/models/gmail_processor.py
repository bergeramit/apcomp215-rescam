"""
Fetches email from Gmail API and processes with model_rag.py
"""
import logging
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from model_rag import classify_email_with_rag

logging.basicConfig(level=logging.INFO)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def parse_email_message(message):
    """Parse Gmail API message format into email content string."""
    payload = message.get('payload', {})
    headers = payload.get('headers', [])
    
    # Extract headers
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
    
    # Extract body
    body = ''
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
            elif part.get('mimeType') == 'text/html' and not body:
                data = part.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    else:
        # Single part message
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    
    # Format email content for model_rag.py
    email_content = f"""From: {sender}
Subject: {subject}
Date: {date}

{body}
"""
    return email_content, {
        'sender': sender,
        'subject': subject,
        'date': date,
        'snippet': message.get('snippet', '')[:200]
    }


def process_email_with_model(message_id, gmail_service, project_id='1097076476714', 
                              location='us-east1', index_endpoint_id='3044332193032699904',
                              deployed_index_id='phishing_emails_deployed_1760372787396'):
    """Fetch email from Gmail and classify it using model_rag.py."""
    try:
        # Fetch message from Gmail
        message = gmail_service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Parse email
        email_content, metadata = parse_email_message(message)
        
        # Classify using model_rag
        # We need to save email to GCS temporarily or pass directly
        # For MVP, we'll create a temporary file path and use GCS
        # Actually, let's modify to pass email content directly to a modified classify function
        
        # For now, save to temporary GCS location
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket('rescam-dataset-bucket')
        
        temp_file_name = f'temp-emails/{message_id}.txt'
        blob = bucket.blob(temp_file_name)
        blob.upload_from_string(email_content)
        
        # Call classification
        result = classify_email_with_rag(
            project_id=project_id,
            location=location,
            index_endpoint_id=index_endpoint_id,
            deployed_index_id=deployed_index_id,
            gcs_bucket_name='rescam-dataset-bucket',
            gcs_file_name=temp_file_name
        )
        
        # Parse result (it's JSON string from Gemini)
        try:
            # Extract JSON from result (Gemini might wrap in markdown)
            if '```json' in result:
                json_start = result.find('```json') + 7
                json_end = result.find('```', json_start)
                result = result[json_start:json_end].strip()
            elif '```' in result:
                json_start = result.find('```') + 3
                json_end = result.find('```', json_start)
                result = result[json_start:json_end].strip()
            
            classification = json.loads(result)
        except:
            # Fallback: try to extract basic info
            classification = {
                'classification': 'unknown',
                'confidence': 0.5,
                'primary_reason': result[:200] if result else 'Classification failed'
            }
        
        # Clean up temp file
        blob.delete()
        
        return {
            'id': message_id,
            'threadId': message.get('threadId', ''),
            'receivedAt': message.get('internalDate', ''),
            'sender': metadata['sender'],
            'subject': metadata['subject'],
            'snippet': metadata['snippet'],
            'body': email_content,
            'classification': classification,
            'processedAt': None  # Will be set by update_gcs
        }
        
    except Exception as e:
        logging.error(f"Error processing email {message_id}: {e}")
        raise

