"""
FastAPI server to handle Eventarc Firestore events
"""
import os
import json
import logging
import base64
from typing import Dict, Any, Tuple
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from google.cloud import firestore, storage
from model_rag import classify_email_with_rag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Firestore client with the specific database ID
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'articulate-fort-472520-p2')
DATABASE_ID = 'user-emails'
COLLECTION_NAME = 'user-emails-incoming'
GCS_BUCKET_NAME = 'rescam-user-emails'

# Model RAG configuration
LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-east1')
INDEX_ENDPOINT_ID = os.getenv('INDEX_ENDPOINT_ID', '3044332193032699904')
DEPLOYED_INDEX_ID = os.getenv('DEPLOYED_INDEX_ID', 'phishing_emails_deployed_1760372787396')

# Initialize Firestore client
db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

# Initialize GCS client
storage_client = storage.Client(project=PROJECT_ID)


def parse_firestore_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Eventarc Firestore event to extract document information.
    
    Eventarc sends CloudEvents in Pub/Sub binding format (CE_PUBSUB_BINDING).
    The event contains a 'message' field with base64-encoded CloudEvent data.
    """
    import base64
    
    try:
        # Handle Pub/Sub binding format (CE_PUBSUB_BINDING)
        if 'message' in event_data:
            message = event_data['message']
            if 'data' in message:
                # Decode base64 CloudEvent data
                decoded_data = base64.b64decode(message['data']).decode('utf-8')
                cloud_event = json.loads(decoded_data)
                
                # CloudEvent has a 'data' field containing the Firestore event
                # Firestore event structure:
                # {
                #   "value": {
                #     "name": "projects/.../databases/.../documents/collection/doc_id",
                #     "fields": {...},
                #     "createTime": "...",
                #     "updateTime": "..."
                #   }
                # }
                firestore_event = cloud_event.get('data', {})
                
                if isinstance(firestore_event, str):
                    # Sometimes data is JSON string
                    firestore_event = json.loads(firestore_event)
                
                if 'value' in firestore_event:
                    value = firestore_event['value']
                    # Extract document path from name
                    # Format: projects/{project}/databases/{database}/documents/{collection}/{doc_id}
                    doc_path = value.get('name', '')
                    if '/documents/' in doc_path:
                        parts = doc_path.split('/documents/')
                        if len(parts) > 1:
                            collection_and_doc = parts[1]
                            path_parts = collection_and_doc.split('/')
                            if len(path_parts) >= 2:
                                collection = path_parts[0]
                                doc_id = path_parts[1]
                                return {
                                    'document_id': doc_id,
                                    'collection': collection,
                                    'full_path': doc_path,
                                    'fields': value.get('fields', {}),
                                    'create_time': value.get('createTime'),
                                    'update_time': value.get('updateTime')
                                }
        
        # Handle direct CloudEvents format (if not using Pub/Sub binding)
        if 'data' in event_data and 'source' in event_data:
            firestore_event = event_data.get('data', {})
            if isinstance(firestore_event, str):
                firestore_event = json.loads(firestore_event)
            
            if 'value' in firestore_event:
                value = firestore_event['value']
                doc_path = value.get('name', '')
                if '/documents/' in doc_path:
                    parts = doc_path.split('/documents/')
                    if len(parts) > 1:
                        collection_and_doc = parts[1]
                        path_parts = collection_and_doc.split('/')
                        if len(path_parts) >= 2:
                            collection = path_parts[0]
                            doc_id = path_parts[1]
                            return {
                                'document_id': doc_id,
                                'collection': collection,
                                'full_path': doc_path,
                                'fields': value.get('fields', {}),
                                'create_time': value.get('createTime'),
                                'update_time': value.get('updateTime')
                            }
        
        logger.warning(f"Could not parse event structure. Keys: {list(event_data.keys())}")
        return None
    except Exception as e:
        logger.error(f"Error parsing Firestore event: {e}", exc_info=True)
        raise


def parse_email_from_gmail_message(raw_email: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Parse Gmail API message format into email content string.
    Similar to gmail_processor.parse_email_message but works with stored raw email.
    
    Returns:
        Tuple of (email_content_string, metadata_dict)
    """
    payload = raw_email.get('payload', {})
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
    metadata = {
        'sender': sender,
        'subject': subject,
        'date': date,
        'snippet': raw_email.get('snippet', '')[:200]
    }
    
    return email_content, metadata


def save_classification_to_gcs(user_id: str, message_id: str, email_metadata: Dict[str, Any], 
                                classification_result: str) -> str:
    """
    Save email classification result to GCS bucket 'rescam-user-emails'.
    
    Args:
        user_id: User email address
        message_id: Gmail message ID
        email_metadata: Metadata about the email (sender, subject, etc.)
        classification_result: JSON string from classify_email_with_rag
        
    Returns:
        GCS path where classification was saved
    """
    try:
        # Parse classification result (it might be wrapped in markdown code blocks)
        classification_json = classification_result
        if '```json' in classification_json:
            json_start = classification_json.find('```json') + 7
            json_end = classification_json.find('```', json_start)
            classification_json = classification_json[json_start:json_end].strip()
        elif '```' in classification_json:
            json_start = classification_json.find('```') + 3
            json_end = classification_json.find('```', json_start)
            classification_json = classification_json[json_start:json_end].strip()
        
        try:
            classification_data = json.loads(classification_json)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning(f"Failed to parse classification JSON, using raw result")
            classification_data = {
                'classification': 'unknown',
                'confidence': 0.5,
                'primary_reason': classification_result[:200] if classification_result else 'Classification failed',
                'raw_result': classification_result
            }
        
        # Prepare email data with classification
        email_data = {
            'id': message_id,
            'threadId': email_metadata.get('thread_id', ''),
            'receivedAt': email_metadata.get('received_at', datetime.utcnow().isoformat() + 'Z'),
            'sender': email_metadata.get('sender', 'Unknown'),
            'subject': email_metadata.get('subject', 'No Subject'),
            'snippet': email_metadata.get('snippet', ''),
            'classification': classification_data,
            'processedAt': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Save to GCS bucket
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        # Path: user-classifications/{user_id}/emails.json
        emails_path = f'user-classifications/{user_id}/emails.json'
        blob = bucket.blob(emails_path)
        
        # Get existing emails
        try:
            existing_data = json.loads(blob.download_as_text())
            emails = existing_data.get('emails', [])
        except:
            emails = []
        
        # Update or add email
        existing_index = next((i for i, e in enumerate(emails) if e['id'] == message_id), None)
        if existing_index is not None:
            emails[existing_index] = email_data
        else:
            emails.insert(0, email_data)  # Add to beginning
        
        # Save back
        blob.upload_from_string(
            json.dumps({'emails': emails}, indent=2),
            content_type='application/json'
        )
        
        logger.info(f"Saved classification for email {message_id} for user {user_id} to {emails_path}")
        return emails_path
        
    except Exception as e:
        logger.error(f"Error saving classification to GCS: {e}", exc_info=True)
        raise


@app.post("/route/firestore-incoming-email")
async def handle_firestore_event(request: Request):
    """
    Handle Eventarc POST event for new Firestore documents.
    Eventarc can send events in either JSON or protobuf format depending on the transport.
    """
    try:
        # Get the content type to determine format
        content_type = request.headers.get("content-type", "").lower()
        
        # Read the raw request body as bytes
        raw_body = await request.body()
        
        body = None
        
        # Try to parse as JSON first (most common case)
        if "application/json" in content_type or not content_type:
            try:
                # Try to decode as UTF-8 and parse as JSON
                body_text = raw_body.decode('utf-8')
                if body_text.strip().startswith(('{', '[')):
                    body = json.loads(body_text)
                    logger.info(f"Parsed Eventarc event as JSON")
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to parse as JSON: {e}, trying protobuf...")
        
        # If JSON parsing failed or content-type indicates protobuf, try protobuf
        if body is None or "application/x-protobuf" in content_type or "application/octet-stream" in content_type:
            try:
                # Try to parse as protobuf using google.cloud.pubsub_v1
                from google.cloud.pubsub_v1.types import PubsubMessage
                from google.protobuf import json_format
                
                # Parse as Pub/Sub message protobuf
                pubsub_message = PubsubMessage()
                pubsub_message.ParseFromString(raw_body)
                
                # Convert protobuf message to dict
                body = json_format.MessageToDict(pubsub_message)
                logger.info(f"Parsed Eventarc event as protobuf (Pub/Sub message)")
                
                # If the message has data, it might be base64-encoded CloudEvent
                if 'data' in body and isinstance(body['data'], str):
                    # The data field in Pub/Sub messages is base64-encoded bytes
                    try:
                        decoded_data = base64.b64decode(body['data']).decode('utf-8')
                        # Try to parse as JSON CloudEvent
                        cloud_event = json.loads(decoded_data)
                        # Replace the data field with the decoded CloudEvent
                        body = {'message': body}
                        body['message']['data'] = decoded_data
                        logger.info(f"Decoded base64-encoded CloudEvent from Pub/Sub message")
                    except Exception as e:
                        logger.warning(f"Could not decode Pub/Sub message data as JSON: {e}")
            except ImportError as e:
                logger.warning(f"Protobuf libraries not available: {e}, trying alternative parsing...")
                # Try to handle as binary data that might contain JSON
                try:
                    # Sometimes the data is just binary-encoded JSON, try to find JSON-like patterns
                    body_text = raw_body.decode('utf-8', errors='ignore')
                    # Look for JSON-like content
                    if '{' in body_text or '[' in body_text:
                        body = json.loads(body_text)
                        logger.info(f"Fallback: parsed binary data as JSON")
                    else:
                        raise ValueError("No JSON-like content found in binary data")
                except Exception as e2:
                    logger.error(f"All parsing attempts failed. Content-Type: {content_type}, Body length: {len(raw_body)}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"Could not parse request body. Content-Type: {content_type}. Error: {str(e2)}"}
                    )
            except Exception as e:
                logger.error(f"Failed to parse as protobuf: {e}")
                # Last resort: try to decode as UTF-8 and parse as JSON
                try:
                    body_text = raw_body.decode('utf-8', errors='ignore')
                    if body_text.strip().startswith(('{', '[')):
                        body = json.loads(body_text)
                        logger.info(f"Fallback: parsed as JSON after protobuf failure")
                    else:
                        raise ValueError("Body does not appear to be JSON")
                except Exception as e2:
                    logger.error(f"All parsing attempts failed. Content-Type: {content_type}, Body length: {len(raw_body)}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"Could not parse request body. Content-Type: {content_type}. Error: {str(e2)}"}
                    )
        
        if body is None:
            logger.error(f"Could not parse request body. Content-Type: {content_type}")
            return JSONResponse(
                status_code=400,
                content={"error": "Could not parse request body"}
            )
        
        logger.info(f"Received Eventarc event: {json.dumps(body, indent=2, default=str)}")
        
        # Parse the Firestore event
        event_info = parse_firestore_event(body)
        
        if not event_info:
            logger.warning("Could not parse Firestore event from request")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid event format"}
            )
        
        document_id = event_info['document_id']
        collection = event_info['collection']
        
        logger.info(f"Processing Firestore event - Collection: {collection}, Document ID: {document_id}")
        
        # Verify it's from the correct collection
        if collection != COLLECTION_NAME:
            logger.warning(f"Event from unexpected collection: {collection}")
            return JSONResponse(
                status_code=200,
                content={"message": f"Ignored event from collection: {collection}"}
            )
        
        # Fetch the document from Firestore
        doc_ref = db.collection(COLLECTION_NAME).document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"Document {document_id} does not exist in Firestore")
            return JSONResponse(
                status_code=404,
                content={"error": f"Document {document_id} not found"}
            )
        
        # Get document data
        doc_data = doc.to_dict()
        user_id = doc_data.get('user-id', 'unknown')
        raw_email = doc_data.get('raw-email', {})
        stored_at = doc_data.get('stored-at', 'unknown')
        message_id = doc_data.get('message-id', document_id)
        
        # Log the email information
        logger.info("=" * 80)
        logger.info(f"Email received from Firestore:")
        logger.info(f"  Document ID: {document_id}")
        logger.info(f"  Message ID: {message_id}")
        logger.info(f"  User ID: {user_id}")
        logger.info(f"  Stored at: {stored_at}")
        
        if not isinstance(raw_email, dict):
            logger.error(f"Raw email is not a dictionary: {type(raw_email)}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid raw email format"}
            )
        
        # Parse email from raw Gmail message
        logger.info("Parsing email from raw Gmail message...")
        try:
            email_content, email_metadata = parse_email_from_gmail_message(raw_email)
            logger.info(f"Email parsed - Subject: {email_metadata['subject']}, From: {email_metadata['sender']}")
        except Exception as e:
            logger.error(f"Error parsing email: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to parse email: {str(e)}"}
            )
        
        # Add thread_id and received_at from raw_email if available
        email_metadata['thread_id'] = raw_email.get('threadId', '')
        if 'internalDate' in raw_email:
            email_metadata['received_at'] = datetime.fromtimestamp(
                int(raw_email['internalDate']) / 1000
            ).isoformat() + 'Z'
        else:
            email_metadata['received_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Save email to temporary GCS location for classification
        logger.info("Saving email to temporary GCS location for classification...")
        temp_bucket_name = 'rescam-dataset-bucket'  # Use existing bucket for temp storage
        temp_file_name = f'temp-emails/{message_id}.txt'
        temp_blob = None
        
        try:
            temp_bucket = storage_client.bucket(temp_bucket_name)
            temp_blob = temp_bucket.blob(temp_file_name)
            temp_blob.upload_from_string(email_content, content_type='text/plain')
            logger.info(f"Email saved to temporary location: gs://{temp_bucket_name}/{temp_file_name}")
        except Exception as e:
            logger.error(f"Error saving email to temp GCS: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to save email to temp GCS: {str(e)}"}
            )
        
        # Classify email using model_rag
        logger.info("Classifying email with RAG model...")
        classification_result = None
        try:
            classification_result = classify_email_with_rag(
                project_id=PROJECT_ID,
                location=LOCATION,
                index_endpoint_id=INDEX_ENDPOINT_ID,
                deployed_index_id=DEPLOYED_INDEX_ID,
                gcs_bucket_name=temp_bucket_name,
                gcs_file_name=temp_file_name
            )
            logger.info(f"Classification complete: {classification_result[:200]}...")
        except Exception as e:
            logger.error(f"Error classifying email: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to classify email: {str(e)}"}
            )
        finally:
            # Clean up temp file
            if temp_blob:
                try:
                    temp_blob.delete()
                    logger.info(f"Cleaned up temporary file: {temp_file_name}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
        
        # Save classification result to GCS bucket 'rescam-user-emails'
        if not classification_result:
            logger.error("Classification result is None, cannot save to GCS")
            return JSONResponse(
                status_code=500,
                content={"error": "Classification failed - no result to save"}
            )
        
        logger.info("Saving classification result to GCS...")
        try:
            gcs_path = save_classification_to_gcs(
                user_id=user_id,
                message_id=message_id,
                email_metadata=email_metadata,
                classification_result=classification_result
            )
            logger.info(f"Classification saved to: gs://{GCS_BUCKET_NAME}/{gcs_path}")
        except Exception as e:
            logger.error(f"Error saving classification to GCS: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to save classification: {str(e)}"}
            )
        
        logger.info("=" * 80)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Email processed and classified successfully",
                "document_id": document_id,
                "user_id": user_id,
                "message_id": message_id,
                "gcs_path": gcs_path
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON format"}
        )
    except Exception as e:
        logger.error(f"Error processing Firestore event: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

