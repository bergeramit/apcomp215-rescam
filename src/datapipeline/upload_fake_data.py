"""
Upload fake email dataset to Google Cloud Storage.
Run this after generating fake emails to test the pipeline.
"""
from google.cloud import storage
import os


def upload_to_gcs(local_file, bucket_name="rescam-dataset-bucket", gcs_folder="raw-datasets"):
    """
    Upload a file to Google Cloud Storage
    
    Args:
        local_file: Path to local file
        bucket_name: GCS bucket name
        gcs_folder: Folder path in GCS (e.g., 'raw-datasets')
    """
    # Initialize GCS client
    storage_client = storage.Client(project='rescam-dataset-bucket')
    bucket = storage_client.get_bucket(bucket_name)
    
    # Create blob path (file path in GCS)
    filename = os.path.basename(local_file)
    blob_path = f"{gcs_folder}/{filename}"
    blob = bucket.blob(blob_path)
    
    # Upload
    print(f"📤 Uploading {local_file} to gs://{bucket_name}/{blob_path}")
    blob.upload_from_filename(local_file)
    print(f"✅ Upload complete!")
    print(f"   GCS path: gs://{bucket_name}/{blob_path}")


if __name__ == "__main__":
    # Upload the fake dataset
    local_file = "raw-datasets/fake_phishing_dataset.csv"
    
    if os.path.exists(local_file):
        upload_to_gcs(local_file)
    else:
        print(f"❌ File not found: {local_file}")
        print("   Run generate_fake_emails.py first!")


