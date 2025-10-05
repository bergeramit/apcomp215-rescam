from google.cloud import storage
import os

def get_raw_files_local() -> list[str]:
    """
    Downloads all the raw files from the bucket to the local machine
    Returns:
        list[str]: List of local file names
    """
    storage_client = storage.Client(project='rescam-dataset-bucket')
    bucket = storage_client.get_bucket('rescam-dataset-bucket')
    folder = bucket.list_blobs(prefix='raw-datasets/')
    print(f"Files in the folder: {folder}")

    os.makedirs('raw-datasets', exist_ok=True)
    os.makedirs('processed-dataset', exist_ok=True)

    for blob in folder:
        print(blob.name)
        full_path = os.path.join('raw-datasets', os.path.basename(blob.name))
        if not blob.name.endswith("/") and not os.path.exists(full_path):
            blob.download_to_filename(full_path)

    print("Done downloading raw files")
    return [os.path.join('raw-datasets', f) for f in os.listdir('raw-datasets')]

def upload_processed_files(processed_dataset_path: str):
    print(f"Uploading {processed_dataset_path} to GCS bucket")
    storage_client = storage.Client(project='rescam-dataset-bucket')
    bucket = storage_client.get_bucket('rescam-dataset-bucket')
    blob = bucket.blob(os.path.join('processed-dataset', os.path.basename(processed_dataset_path)))
    blob.upload_from_filename(processed_dataset_path)
