# Tests

This directory contains test scripts and test data for validating various components of the Rescam system.

## Directory Structure

```
tests/
├── models/              # Tests for the models service
│   ├── README.md        # Models test documentation
│   ├── test_firestore_event.sh  # Firestore event handler test
│   └── example_firestore_event_message.b64 # Test data (base64-encoded protobuf)
└── README.md           # This file
```

## Running Tests

### Models Service Tests

See [models/README.md](./models/README.md) for detailed documentation on testing the models service.

Quick start:
```bash
cd tests/models
./test_firestore_event.sh
```

## Adding New Tests

When adding new tests:
1. Create a dedicated subdirectory for the component being tested
2. Include a README.md with usage instructions
3. Make test scripts executable (`chmod +x`)
4. Document prerequisites and expected behavior

