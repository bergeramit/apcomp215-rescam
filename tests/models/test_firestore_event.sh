#!/bin/bash

# Test script for Firestore event handler endpoint
# Sends a base64-encoded protobuf message to validate the models service
#
# Usage:
#   ./test_firestore_event.sh [ENDPOINT_URL] [BASE64_FILE]
#
# Examples:
#   ./test_firestore_event.sh
#   ./test_firestore_event.sh http://localhost:8080/route/firestore-incoming-email
#   ./test_firestore_event.sh http://localhost:8080/route/firestore-incoming-email example_firestore_event_message.b64

set -euo pipefail

# Get script directory to find test data relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
DEFAULT_ENDPOINT="${ENDPOINT_URL:-http://localhost:8080/route/firestore-incoming-email}"
DEFAULT_B64_FILE="${BASE64_FILE:-${SCRIPT_DIR}/example_firestore_event_message.b64}"

# Parse arguments
ENDPOINT_URL="${1:-$DEFAULT_ENDPOINT}"
B64_FILE="${2:-$DEFAULT_B64_FILE}"

# Resolve relative paths
if [[ ! "$B64_FILE" =~ ^/ ]]; then
    B64_FILE="${SCRIPT_DIR}/${B64_FILE}"
fi

# Validation
if [ ! -f "$B64_FILE" ]; then
    echo "❌ Error: Base64 file not found: $B64_FILE" >&2
    exit 1
fi

for cmd in curl base64; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Error: $cmd is not installed!" >&2
        exit 1
    fi
done

# Display test information
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Firestore Event Handler Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Endpoint: $ENDPOINT_URL"
echo "Test data: $B64_FILE"
echo ""

# Decode base64 to binary
echo "📦 Decoding base64 protobuf..."
PROTOBUF_BINARY=$(mktemp)
trap "rm -f '$PROTOBUF_BINARY'" EXIT

if ! base64 -di "$B64_FILE" > "$PROTOBUF_BINARY" 2>/dev/null; then
    echo "❌ Error: Failed to decode base64 file" >&2
    exit 1
fi

FILE_SIZE=$(wc -c < "$PROTOBUF_BINARY" | tr -d ' ')
echo "   Decoded size: $FILE_SIZE bytes"
echo ""

# Prepare request
FULL_URL="${ENDPOINT_URL}?__GCP_CloudEventsMode=CE_PUBSU_"

echo "📤 Sending POST request..."
echo ""

# Send request and capture response
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/protobuf" \
    -H "User-Agent: APIs-Google; (+https://developers.google.com/webmasters/APIs-Google.html)" \
    -H "X-Cloud-Trace-Context: test-trace-id/1234567890123456789;o=1" \
    --data-binary "@$PROTOBUF_BINARY" \
    "$FULL_URL" \
    2>&1) || {
    echo "❌ Error: Failed to send request" >&2
    exit 1
}

# Extract HTTP status code and response body
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

# Display results
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 Response"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "HTTP Status: $HTTP_CODE"
echo ""

if [ -n "$RESPONSE_BODY" ]; then
    echo "Response Body:"
    if command -v jq &> /dev/null; then
        echo "$RESPONSE_BODY" | jq '.' 2>/dev/null || echo "$RESPONSE_BODY"
    else
        echo "$RESPONSE_BODY"
    fi
    echo ""
fi

# Determine exit status
if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "✅ Test passed! (HTTP $HTTP_CODE)"
    exit 0
else
    echo "❌ Test failed! (HTTP $HTTP_CODE)"
    exit 1
fi

