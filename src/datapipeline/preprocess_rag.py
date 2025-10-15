"""
Preprocess emails for RAG using Vertex AI Vector Search
- Downloads email data from GCS
- Generates embeddings for email content
- Stores in Vertex AI Vector Search for production-scale similarity search
"""
import pandas as pd
import os
import json
import time
from google.cloud import storage
from google.cloud import aiplatform
from sentence_transformers import SentenceTransformer
import numpy as np

# Vertex AI configuration
PROJECT_ID = "1097076476714"  # Your GCP project ID
REGION = "us-central1"  # Vertex AI region
BUCKET_NAME = "rescam-rag-bucket"  # Bucket for RAG embeddings (us-central1)


def download_user_emails_from_gcs(bucket_name=BUCKET_NAME, 
                                    gcs_folder="user_emails",
                                    local_folder="user_emails"):
    """
    Download email CSV files from the user_emails folder in GCS
    
    Args:
        bucket_name: GCS bucket name
        gcs_folder: Folder path in GCS where user emails are stored
        local_folder: Local folder to download to
    
    Returns:
        list: Paths to downloaded CSV files
    """
    print(f"📥 Downloading emails from gs://{bucket_name}/{gcs_folder}/")
    
    # Initialize GCS client
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.get_bucket(bucket_name)
    
    # Create local folder
    os.makedirs(local_folder, exist_ok=True)
    
    # List all blobs in the folder
    blobs = bucket.list_blobs(prefix=f"{gcs_folder}/")
    
    downloaded_files = []
    for blob in blobs:
        # Skip the folder itself
        if blob.name.endswith("/"):
            continue
            
        # Download file
        filename = os.path.basename(blob.name)
        local_path = os.path.join(local_folder, filename)
        
        if not os.path.exists(local_path):
            print(f"  Downloading: {blob.name}")
            blob.download_to_filename(local_path)
            downloaded_files.append(local_path)
        else:
            print(f"  Already exists: {local_path}")
            downloaded_files.append(local_path)
    
    print(f"✅ Downloaded {len(downloaded_files)} file(s)")
    return downloaded_files


def load_emails(file_paths):
    """
    Load email CSV files into a single DataFrame
    
    Args:
        file_paths: List of paths to CSV files
    
    Returns:
        pd.DataFrame: Combined email data
    """
    print(f"\n📊 Loading email data from {len(file_paths)} file(s)...")
    
    all_emails = []
    for file_path in file_paths:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            print(f"  Loaded {len(df)} emails from {os.path.basename(file_path)}")
            all_emails.append(df)
        elif file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
            print(f"  Loaded {len(df)} emails from {os.path.basename(file_path)}")
            all_emails.append(df)
    
    if not all_emails:
        raise ValueError("No email data found!")
    
    combined_df = pd.concat(all_emails, ignore_index=True)
    print(f"✅ Total emails loaded: {len(combined_df)}")
    print(f"   Columns: {list(combined_df.columns)}")
    
    return combined_df


def prepare_text_for_embedding(df):
    """
    Combine email fields into text suitable for embedding
    
    Args:
        df: DataFrame with email data
    
    Returns:
        pd.DataFrame: DataFrame with added 'combined_text' column
    """
    print(f"\n📝 Preparing text for embedding...")
    
    # Strategy: Combine subject and body
    df['combined_text'] = df.apply(
        lambda row: f"Subject: {row['subject']}\n\n{row['body']}", 
        axis=1
    )
    
    # Show sample
    print(f"   Sample combined text:")
    print(f"   {df['combined_text'].iloc[0][:200]}...")
    
    return df


def generate_embeddings(df, model_name="all-MiniLM-L6-v2"):
    """
    Generate embeddings for email text using sentence-transformers
    
    Args:
        df: DataFrame with 'combined_text' column
        model_name: Name of embedding model to use
    
    Returns:
        pd.DataFrame: DataFrame with added 'embedding' column
    """
    print(f"\n🔢 Generating embeddings using {model_name}...")
    
    # Load the embedding model
    print(f"   Loading model (first time will download ~80-400MB)...")
    model = SentenceTransformer(model_name)
    
    # Generate embeddings
    texts = df['combined_text'].tolist()
    print(f"   Encoding {len(texts)} emails...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    # Add to dataframe
    df['embedding'] = embeddings.tolist()
    
    print(f"✅ Generated embeddings with dimension: {embeddings.shape[1]}")
    print(f"   Embedding shape: {embeddings.shape}")
    
    return df


def upload_embeddings_to_vertex_ai(df, index_name="phishing-email-index"):
    """
    Upload embeddings to Vertex AI Vector Search
    
    This creates a JSON lines file in GCS that Vertex AI can index
    
    Args:
        df: DataFrame with embeddings and metadata
        index_name: Name for the index
    
    Returns:
        str: GCS path to the uploaded embeddings file
    """
    print(f"\n💾 Preparing embeddings for Vertex AI Vector Search...")
    
    # Create JSONL format for Vertex AI
    # Format: {"id": "email_0", "embedding": [...]}
    # Simple format for Tree-AH algorithm
    jsonl_data = []
    
    for idx, row in df.iterrows():
        item = {
            "id": f"email_{idx}",
            "embedding": row['embedding'],  # List of floats
        }
        jsonl_data.append(item)
    
    # Save to local file (use .json extension for Vertex AI)
    local_jsonl_path = "embeddings_for_vertex_ai.json"
    print(f"   Writing {len(jsonl_data)} items to {local_jsonl_path}...")
    
    with open(local_jsonl_path, 'w') as f:
        for item in jsonl_data:
            f.write(json.dumps(item) + '\n')
    
    # Upload to GCS (in dedicated clean folder for Vertex AI)
    gcs_path = f"gs://{BUCKET_NAME}/vertex_ai_index_data/{local_jsonl_path}"
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"vertex_ai_index_data/{local_jsonl_path}")
    
    print(f"   Uploading to {gcs_path}...")
    blob.upload_from_filename(local_jsonl_path)
    
    print(f"✅ Embeddings uploaded to GCS: {gcs_path}")
    
    # Also save metadata separately for easy access (in separate folder)
    metadata_df = df[['sender', 'subject', 'label', 'spam_flag', 'urls', 'date', 'combined_text']].copy()
    metadata_df['email_id'] = [f"email_{i}" for i in range(len(metadata_df))]
    metadata_path = "email_metadata.parquet"
    metadata_df.to_parquet(metadata_path, index=False)
    
    # Upload metadata to SEPARATE folder (Vertex AI only reads vertex_ai_embeddings/)
    blob_meta = bucket.blob(f"metadata/{metadata_path}")
    blob_meta.upload_from_filename(metadata_path)
    print(f"✅ Metadata uploaded: gs://{BUCKET_NAME}/metadata/{metadata_path}")
    
    return gcs_path


def create_vertex_ai_index(gcs_embeddings_path, index_display_name="phishing-email-index", 
                           dimensions=384, approximate_neighbors_count=10):
    """
    Create a Vertex AI Vector Search Index
    
    NOTE: This is a one-time setup. The index can be reused.
    
    Args:
        gcs_embeddings_path: GCS path to embeddings JSONL file
        index_display_name: Display name for the index
        dimensions: Embedding dimension (384 for all-MiniLM-L6-v2)
        approximate_neighbors_count: Number of neighbors for ANN
    
    Returns:
        aiplatform.MatchingEngineIndex: Created index
    """
    print(f"\n🏗️  Creating Vertex AI Vector Search Index...")
    print(f"   This may take 20-40 minutes for the index to build...")
    
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=REGION)
    
    # Create index config
    index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
        display_name=index_display_name,
        contents_delta_uri=gcs_embeddings_path.rsplit('/', 1)[0],  # Folder path
        dimensions=dimensions,
        approximate_neighbors_count=approximate_neighbors_count,
        description="Phishing email detection vector search index",
        labels={"env": "dev", "project": "rescam"},
    )
    
    print(f"✅ Index created: {index.display_name}")
    print(f"   Resource name: {index.resource_name}")
    print(f"   Index will be available once building completes")
    
    return index


def deploy_index_to_endpoint(index, endpoint_display_name="phishing-email-endpoint"):
    """
    Deploy the index to an endpoint for querying
    
    Args:
        index: MatchingEngineIndex to deploy
        endpoint_display_name: Display name for endpoint
    
    Returns:
        aiplatform.MatchingEngineIndexEndpoint: Deployed endpoint
    """
    print(f"\n🚀 Deploying index to endpoint...")
    print(f"   This may take 10-20 minutes...")
    
    # Create endpoint
    endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
        display_name=endpoint_display_name,
        description="Endpoint for phishing email vector search",
        public_endpoint_enabled=True,
    )
    
    print(f"✅ Endpoint created: {endpoint.display_name}")
    
    # Deploy index to endpoint
    endpoint = endpoint.deploy_index(
        index=index,
        deployed_index_id="phishing_emails_deployed",
        display_name="Phishing Emails Index",
        machine_type="e2-standard-2",
        min_replica_count=1,
        max_replica_count=1,
    )
    
    print(f"✅ Index deployed to endpoint")
    print(f"   Endpoint resource name: {endpoint.resource_name}")
    
    return endpoint


def main():
    """
    Main RAG preprocessing pipeline for Vertex AI
    """
    print("=" * 70)
    print("RAG Preprocessing Pipeline - Vertex AI Vector Search")
    print("=" * 70)
    
    # Step 1: Download emails from GCS (from the original bucket)
    email_files = download_user_emails_from_gcs(
        bucket_name="rescam-dataset-bucket",  # Original bucket with emails
        gcs_folder="user_emails",
        local_folder="user_emails"
    )
    
    # Step 2: Load email data
    df = load_emails(email_files)
    
    # Step 3: Prepare text for embedding
    df = prepare_text_for_embedding(df)
    
    # Step 4: Generate embeddings
    df = generate_embeddings(df)
    
    # Step 5: Upload embeddings to GCS for Vertex AI
    gcs_path = upload_embeddings_to_vertex_ai(df)
    
    print("\n" + "=" * 70)
    print("✅ Embeddings Ready for Vertex AI!")
    print("=" * 70)
    print(f"\nWhat was created:")
    print(f"  - Processed {len(df)} emails")
    print(f"  - Generated {len(df)} embeddings (384 dimensions)")
    print(f"  - Uploaded to: {gcs_path}")
    
    print(f"\n📋 Next Steps (Manual - One Time Setup):")
    print(f"\n1. Create Index in Vertex AI Console:")
    print(f"   https://console.cloud.google.com/vertex-ai/matching-engine/indexes")
    print(f"   - Click 'CREATE INDEX'")
    print(f"   - Name: phishing-email-index")
    print(f"   - Input data: {gcs_path}")
    print(f"   - Dimensions: 384")
    print(f"   - Algorithm: Tree-AH (recommended for < 100K vectors)")
    print(f"   - Wait ~30 minutes for index to build")
    
    print(f"\n2. Create Endpoint:")
    print(f"   - Click 'CREATE ENDPOINT'")
    print(f"   - Name: phishing-email-endpoint")
    print(f"   - Region: {REGION}")
    
    print(f"\n3. Deploy Index to Endpoint:")
    print(f"   - Select your index")
    print(f"   - Deploy to the endpoint you created")
    print(f"   - Machine type: e2-standard-2")
    print(f"   - Min replicas: 1")
    
    print(f"\n4. Query the index using query_vertex_ai.py")
    
    print(f"\n💡 Alternative: Automated setup (uncomment create_vertex_ai_index below)")


if __name__ == "__main__":
    main()
    
    # Uncomment below for automated index creation (takes 30+ minutes)
    # NOTE: This will incur costs!
    """
    print("\n⚠️  Starting automated index creation...")
    index = create_vertex_ai_index(
        gcs_embeddings_path="gs://rescam-dataset-bucket/vertex_ai_embeddings/embeddings_for_vertex_ai.jsonl",
        dimensions=384
    )
    
    # Wait for index to be ready (optional - can check console instead)
    print("Waiting for index to be ready...")
    # endpoint = deploy_index_to_endpoint(index)
    """
