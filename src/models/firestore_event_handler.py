"""
FastAPI server to handle Eventarc Firestore events
"""
import os
import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from google.cloud import firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Firestore client with the specific database ID
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'articulate-fort-472520-p2')
DATABASE_ID = 'user-emails'
COLLECTION_NAME = 'user-emails-incoming'

# Initialize Firestore client
db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)


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


@app.post("/route/firestore-incoming-email")
async def handle_firestore_event(request: Request):
    """
    Handle Eventarc POST event for new Firestore documents.
    """
    try:
        # Get the raw request body
        body = await request.json()
        logger.info(f"Received Eventarc event: {json.dumps(body, indent=2)}")
        
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
        logger.info(f"  Raw email keys: {list(raw_email.keys()) if isinstance(raw_email, dict) else 'N/A'}")
        
        # Log raw email content (can be large, so log summary)
        if isinstance(raw_email, dict):
            # Extract subject from headers
            subject = 'N/A'
            if 'payload' in raw_email and 'headers' in raw_email['payload']:
                headers = raw_email['payload']['headers']
                subject_header = next((h for h in headers if h.get('name', '').lower() == 'subject'), None)
                if subject_header:
                    subject = subject_header.get('value', 'N/A')
            
            snippet = raw_email.get('snippet', 'N/A')
            logger.info(f"  Email subject: {subject}")
            logger.info(f"  Email snippet: {snippet}")
            logger.info(f"  Full raw email structure: {json.dumps(raw_email, indent=2, default=str)}")
        else:
            logger.info(f"  Raw email: {raw_email}")
        
        logger.info("=" * 80)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Email processed successfully",
                "document_id": document_id,
                "user_id": user_id,
                "message_id": message_id
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

