#!/bin/bash

# Script to send a base64-encoded protobuf message to the firestore_event_handler endpoint
# Usage: ./test_firestore_event.sh [ENDPOINT_URL] [BASE64_FILE]

set -e

# Default values
DEFAULT_ENDPOINT="${ENDPOINT_URL:-http://localhost:8080/route/firestore-incoming-email}"
DEFAULT_B64_FILE="${BASE64_FILE:-test_message.b64}"

# Parse arguments
ENDPOINT_URL="${1:-$DEFAULT_ENDPOINT}"
B64_FILE="${2:-$DEFAULT_B64_FILE}"

# Check if base64 file exists
if [ ! -f "$B64_FILE" ]; then
    echo "Error: Base64 file '$B64_FILE' not found!"
    exit 1
fi

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed!"
    exit 1
fi

# Check if base64 is available
if ! command -v base64 &> /dev/null; then
    echo "Error: base64 is not installed!"
    exit 1
fi

echo "=========================================="
echo "Sending protobuf message to firestore_event_handler"
echo "=========================================="
echo "Endpoint: $ENDPOINT_URL"
echo "Base64 file: $B64_FILE"
echo ""

# Read and decode base64 to binary
echo "Decoding base64 protobuf..."
PROTOBUF_BINARY=$(mktemp)
base64 -di "$B64_FILE" > "$PROTOBUF_BINARY"

# Get file size for logging
FILE_SIZE=$(wc -c < "$PROTOBUF_BINARY")
echo "Decoded protobuf size: $FILE_SIZE bytes"
echo ""

# Send the request
echo "Sending POST request..."
echo ""

# Include the query parameter that Eventarc uses
FULL_URL="${ENDPOINT_URL}?__GCP_CloudEventsMode=CE_PUBSU_"

# Send with curl
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/protobuf" \
    -H "User-Agent: APIs-Google; (+https://developers.google.com/webmasters/APIs-Google.html)" \
    -H "X-Cloud-Trace-Context: test-trace-id/1234567890123456789;o=1" \
    --data-binary "@$PROTOBUF_BINARY" \
    "$FULL_URL" \
    2>&1)

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
# Extract response body (all but last line)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

# Clean up temp file
rm -f "$PROTOBUF_BINARY"

echo "=========================================="
echo "Response:"
echo "=========================================="
echo "HTTP Status Code: $HTTP_CODE"
echo ""
echo "Response Body:"
echo "$RESPONSE_BODY" | jq '.' 2>/dev/null || echo "$RESPONSE_BODY"
echo ""

# Check if request was successful
if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "✅ Request successful!"
    exit 0
else
    echo "❌ Request failed with status code: $HTTP_CODE"
    exit 1
fi

