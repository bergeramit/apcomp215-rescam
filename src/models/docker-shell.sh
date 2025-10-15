#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Define some environment variables
export IMAGE_NAME="ml-model"
export BASE_DIR=$(pwd)
export PROJECT_ROOT="$(cd ../../ && pwd)"

# Change to project root and build
cd "$PROJECT_ROOT"
docker build -t $IMAGE_NAME -f src/models/Dockerfile .
#docker build -t $IMAGE_NAME --platform=linux/amd64 -f src/models/Dockerfile .

# Run the container
docker run --rm --name $IMAGE_NAME -ti $IMAGE_NAME