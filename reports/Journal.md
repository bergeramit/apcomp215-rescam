# Day 1

## Setup

- Created a virtual environment
- Installed the required packages
- Had to install google-cloud-storage using uv add google-cloud-storage -> to be added to pyproject.toml
- To access the bucket, I had to first install gcloud SDK and then authenticate using gcloud auth login
The CLI I ran to authenticate was:
```
gcloud init
gcloud auth application-default login
gcloud config set project 1097076476714 # --> Project ID
gcloud auth application-default set-quota-project 1097076476714 # --> Project ID
```
This created the files in [./secrets/application_default_credentials.json] and [/Users/amitberger/.config/gcloud/config.yaml]

Find out that Parquet is the best format for storing data in this case, as it is the most compact and efficient format for storing data in a tabular format.

To access GSC from within the container, I had to copy the credentials to the container and set the environment variable GOOGLE_APPLICATION_CREDENTIALS to point to the credentials file.

There are more secure (for production) ways to do so:
Option 1: Use Service Account Key (Recommended for production)
```
gcloud iam service-accounts create rescam-docker-sa
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:rescam-docker-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=rescam-docker-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy service account key
COPY --chown=app:app service-account-key.json /home/app/service-account-key.json

# Set environment variable for Google Application Credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/home/app/service-account-key.json"
```
Option 2: Use Environment Variables (Most secure for production)
```
docker run -v ~/.config/gcloud:/home/app/.config/gcloud:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS="./secrets/application_default_credentials.json" \
  your-image-name
```
Most secure: Use Google Cloud Run or Kubernetes with Workload Identity to avoid copying any credentials

To make it hacky used the following command:
```
cp ~/.config/gcloud/application_default_credentials.json src/datapipeline/secrets/application_default_credentials.json
```
and then copying this to the docker