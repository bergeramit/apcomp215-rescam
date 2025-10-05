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
This created the files in [/Users/amitberger/.config/gcloud/application_default_credentials.json] and [/Users/amitberger/.config/gcloud/config.yaml]

Find out that Parquet is the best format for storing data in this case, as it is the most compact and efficient format for storing data in a tabular format.