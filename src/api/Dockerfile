FROM node:20-alpine
# Install Python and dependencies for model_rag.py
RUN apk add --no-cache python3 py3-pip
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
# Create gcloud config directory for credentials (volume mount will provide the file)
RUN mkdir -p /home/app/.config/gcloud
# Note: Credentials are provided via volume mount in docker-compose.yml
# The GOOGLE_APPLICATION_CREDENTIALS environment variable points to the mounted file
# Note: model_rag.py expects Python dependencies - these should be installed
# For MVP, you may need to install them here or mount a Python container
EXPOSE 5050
CMD ["npm", "start"]

