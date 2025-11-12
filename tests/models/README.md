# Models Service Tests

This directory contains tests for validating the models Docker service, specifically the Firestore event handler endpoint.

## Test: Firestore Event Handler

### Overview

The `test_firestore_event.sh` script sends a base64-encoded protobuf message to the Firestore event handler endpoint to validate that the models service is working correctly.

### Prerequisites

- `curl` - for making HTTP requests
- `base64` - for decoding the test message
- `jq` (optional) - for pretty-printing JSON responses

### Usage

#### Basic Usage (uses defaults)

```bash
cd tests/models
./test_firestore_event.sh
```

This will:
- Use the default endpoint: `http://localhost:8080/route/firestore-incoming-email`
- Use the default test data: `test_message.b64`

#### Custom Endpoint

```bash
./test_firestore_event.sh http://localhost:8080/route/firestore-incoming-email
```

#### Custom Endpoint and Test Data

```bash
./test_firestore_event.sh http://localhost:8080/route/firestore-incoming-email test_message.b64
```

#### Using Environment Variables

```bash
export ENDPOINT_URL="http://localhost:8080/route/firestore-incoming-email"
export BASE64_FILE="test_message.b64"
./test_firestore_event.sh
```

### What It Tests

The script validates:
1. ✅ The models service is running and accessible
2. ✅ The Firestore event handler endpoint accepts protobuf messages
3. ✅ The endpoint correctly processes Firestore document events
4. ✅ The response format is valid

### Test Data

The `test_message.b64` file contains a base64-encoded protobuf message that simulates a Firestore document event. This represents a typical email document that would be created in Firestore when a new email arrives.

### Expected Output

On success, you should see:
```
✅ Test passed! (HTTP 200)
```

On failure, you'll see:
```
❌ Test failed! (HTTP <status_code>
```

### Troubleshooting

**Connection refused:**
- Ensure the models Docker container is running
- Check that the endpoint URL is correct
- Verify the service is listening on the expected port

**Invalid protobuf:**
- Ensure `test_message.b64` is not corrupted
- Check that the base64 encoding is valid

**404 Not Found:**
- Verify the route path is correct: `/route/firestore-incoming-email`
- Check that the FastAPI application has the route registered

### Integration with CI/CD

This test can be easily integrated into CI/CD pipelines:

```bash
#!/bin/bash
# Example CI script
cd tests/models
./test_firestore_event.sh "${MODELS_ENDPOINT}" || exit 1
```

