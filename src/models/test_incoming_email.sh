#!/bin/bash

# Sample Eventarc event in Pub/Sub binding format
# This simulates what Eventarc sends when a Firestore document is created

MESSAGE_DATA=$(cat <<EOF
{
  "message": {
    "data": "$(echo -n '{
      "specversion": "1.0",
      "type": "google.cloud.firestore.document.v1.written",
      "source": "//firestore.googleapis.com/projects/articulate-fort-472520-p2/databases/user-emails",
      "id": "test-event-id",
      "time": "2025-01-09T20:00:00Z",
      "data": {
        "value": {
          "name": "projects/articulate-fort-472520-p2/databases/user-emails/documents/user-emails-incoming/19a6a3b201355576",
          "createTime": "2025-01-09T20:00:00Z",
          "updateTime": "2025-01-09T20:00:00Z"
        }
      }
    }' | base64 | tr -d '\n')",
    "messageId": "test-message-id",
    "publishTime": "2025-01-09T20:00:00Z"
  },
  "subscription": "projects/articulate-fort-472520-p2/subscriptions/test-sub"
}
EOF
)

curl -X POST http://localhost:8080/route/firestore-incoming-email \
  -H "Content-Type: application/json" \
  -d "$MESSAGE_DATA"