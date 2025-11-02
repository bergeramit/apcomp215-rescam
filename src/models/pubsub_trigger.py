"""
Pub/Sub subscriber that triggers model_rag.py when Gmail notifications arrive
"""
import os
import json
import logging
from google.cloud import pubsub_v1
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from gmail_processor import process_email_with_model
from update_gcs import save_email_classification

logging.basicConfig(level=logging.INFO)

PROJECT_ID = os.getenv('GCP_PROJECT_ID', '1097076476714')
SUBSCRIPTION_NAME = os.getenv('PUBSUB_SUBSCRIPTION_NAME', 'gmail-classification-trigger')

# For MVP, we'll use service account credentials
# In production, should use OAuth tokens per user
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 
                                  './secrets/application_default_credentials.json')


def get_gmail_service():
    """Get Gmail API service using service account."""
    # Note: Service accounts can't access user Gmail directly
    # For MVP, we assume OAuth tokens are stored and refreshed via backend
    # This is a simplified version - in production, fetch user's OAuth token from backend/DB
    
    # For now, we'll need to get user tokens from the backend API
    # This subscriber will need to be updated to fetch tokens per user
    # For MVP, we'll make an HTTP call to backend to get Gmail client
    # OR store OAuth tokens in a way this can access
    
    # Simplified: Assume we can use the service account or get tokens via API
    # For now, this will fail - user needs to provide OAuth tokens
    raise NotImplementedError(
        "Gmail API requires user OAuth tokens. "
        "This needs to be integrated with backend token store."
    )


def process_message(message_data):
    """Process a Pub/Sub message containing Gmail notification."""
    try:
        user_email = message_data.get('emailAddress')
        history_id = message_data.get('historyId')
        message_ids = message_data.get('messageIds', [])
        
        if not user_email:
            logging.error("Missing user email in message")
            return
        
        if not message_ids:
            logging.info(f"No message IDs in notification for {user_email}")
            return
        
        logging.info(f"Processing {len(message_ids)} messages for {user_email}")
        
        # Get Gmail service (this needs OAuth tokens - simplified for MVP)
        # TODO: Fetch user's OAuth token from backend/token store
        gmail_service = get_gmail_service()
        
        # Process each message
        for message_id in message_ids:
            try:
                # Fetch and classify email
                email_data = process_email_with_model(
                    message_id=message_id,
                    gmail_service=gmail_service,
                    project_id=PROJECT_ID
                )
                
                # Save to GCS
                save_email_classification(user_email, email_data)
                
                logging.info(f"Processed email {message_id} for {user_email}")
                
            except Exception as e:
                logging.error(f"Error processing message {message_id}: {e}")
                continue
        
    except Exception as e:
        logging.error(f"Error processing Pub/Sub message: {e}")


def subscribe():
    """Subscribe to Pub/Sub and process messages."""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
    
    def callback(message):
        try:
            # Decode message
            data = json.loads(message.data.decode('utf-8'))
            logging.info(f"Received message: {data}")
            
            # Process message
            process_message(data)
            
            # Acknowledge
            message.ack()
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            message.nack()
    
    logging.info(f"Subscribing to {subscription_path}")
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        logging.info("Subscription cancelled")


if __name__ == '__main__':
    subscribe()

