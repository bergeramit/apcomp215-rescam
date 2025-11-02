"""
Updates GCS bucket with email classification results
"""
import json
import logging
from datetime import datetime
from google.cloud import storage

logging.basicConfig(level=logging.INFO)


def save_email_classification(user_email, email_data, bucket_name='rescam-dataset-bucket'):
    """Save or update email classification in GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Set processed timestamp
    email_data['processedAt'] = datetime.utcnow().isoformat() + 'Z'
    
    # Path for user's email classifications
    emails_path = f'email-classifications/{user_email}/emails.json'
    blob = bucket.blob(emails_path)
    
    # Get existing emails
    try:
        existing_data = json.loads(blob.download_as_text())
        emails = existing_data.get('emails', [])
    except:
        emails = []
    
    # Update or add email
    existing_index = next((i for i, e in enumerate(emails) if e['id'] == email_data['id']), None)
    if existing_index is not None:
        emails[existing_index] = email_data
    else:
        emails.insert(0, email_data)  # Add to beginning
    
    # Save back
    blob.upload_from_string(
        json.dumps({'emails': emails}, indent=2),
        content_type='application/json'
    )
    
    # Update timestamp file
    timestamp_path = f'email-classifications/{user_email}/latest-timestamp.txt'
    timestamp_blob = bucket.blob(timestamp_path)
    timestamp_blob.upload_from_string(
        str(int(datetime.utcnow().timestamp() * 1000)),
        content_type='text/plain'
    )
    
    logging.info(f"Saved classification for email {email_data['id']} for user {user_email}")
    return email_data

