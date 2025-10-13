"""
Query Vertex AI Vector Search for similar emails
Run this after index is deployed to test retrieval
"""
from google.cloud import aiplatform
from sentence_transformers import SentenceTransformer
import pandas as pd

# Configuration
PROJECT_ID = "1097076476714"
REGION = "us-east1"
ENDPOINT_ID = 3044332193032699904  # TODO: Get this from Vertex AI Console after deployment
INDEX_ENDPOINT_NAME = f"projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{ENDPOINT_ID}"


def query_similar_emails(query_text, endpoint_name, num_neighbors=5):
    """
    Find emails similar to the query text
    
    Args:
        query_text: Text to search for
        endpoint_name: Full resource name of the deployed index endpoint
        num_neighbors: Number of similar emails to return
    
    Returns:
        list: Search results with IDs and distances
    """
    print(f"\n🔍 Querying Vertex AI Vector Search...")
    print(f"   Query: \"{query_text}\"")
    
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=REGION)
    
    # Load embedding model (same one used for indexing)
    print(f"   Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Generate query embedding
    query_embedding = model.encode([query_text], convert_to_numpy=True)[0]
    print(f"   Generated query embedding: {query_embedding.shape}")
    
    # Get the endpoint
    endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
    
    # Query the index
    print(f"   Searching for {num_neighbors} similar emails...")
    response = endpoint.find_neighbors(
        deployed_index_id="phishing_emails_deployed_1760372787396",
        queries=[query_embedding.tolist()],
        num_neighbors=num_neighbors,
    )
    
    print(f"\n✅ Found {len(response[0])} results")
    
    return response[0]


def display_results(results, metadata_path="email_metadata.parquet"):
    """
    Display search results with metadata
    
    Args:
        results: List of MatchNeighbor objects
        metadata_path: Path to metadata parquet file
    """
    print("\n" + "=" * 70)
    print("Search Results:")
    print("=" * 70)
    
    # Load metadata
    try:
        metadata_df = pd.read_parquet(metadata_path)
        has_metadata = True
    except:
        print("⚠️  Metadata file not found - showing IDs only")
        has_metadata = False
    
    for i, neighbor in enumerate(results):
        print(f"\n📧 Result #{i+1}")
        print(f"   ID: {neighbor.id}")
        print(f"   Distance: {neighbor.distance:.4f} (lower = more similar)")
        
        if has_metadata:
            # Find matching metadata
            email_data = metadata_df[metadata_df['email_id'] == neighbor.id]
            if not email_data.empty:
                row = email_data.iloc[0]
                print(f"   Sender: {row['sender']}")
                print(f"   Subject: {row['subject']}")
                print(f"   Label: {'🚨 PHISHING' if row['label'] == 1 else '✅ LEGITIMATE'}")
                print(f"   Spam Flag: {'⚠️ Marked as spam' if row.get('spam_flag', 0) == 1 else 'Not flagged'}")
                print(f"   Content: {row['combined_text'][:200]}...")
    
    print("\n" + "=" * 70)


def main():
    """
    Example queries
    """
    # Check if endpoint is configured
    if not INDEX_ENDPOINT_NAME:
        print("=" * 70)
        print("⚠️  Endpoint Not Configured")
        print("=" * 70)
        print("\nTo use this script:")
        print("1. Deploy your index in Vertex AI Console")
        print("2. Get the endpoint resource name")
        print("3. Set INDEX_ENDPOINT_NAME in this file")
        print("\nFormat:")
        print("   projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{ENDPOINT_ID}")
        print("\nFind it at:")
        print("   https://console.cloud.google.com/vertex-ai/matching-engine/index-endpoints")
        return
    
    print("=" * 70)
    print("Vertex AI Vector Search - Query Test")
    print("=" * 70)
    
    # Test query 1: Phishing-like
    print("\n🎯 Test 1: Phishing pattern search")
    results = query_similar_emails(
        query_text="Click here to verify your account immediately",
        endpoint_name=INDEX_ENDPOINT_NAME,
        num_neighbors=3
    )
    display_results(results)
    
    # Test query 2: Legitimate
    print("\n\n🎯 Test 2: Legitimate email search")
    results = query_similar_emails(
        query_text="Weekly team meeting notes and updates",
        endpoint_name=INDEX_ENDPOINT_NAME,
        num_neighbors=3
    )
    display_results(results)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Custom query from command line
        if not INDEX_ENDPOINT_NAME:
            print("Error: Set INDEX_ENDPOINT_NAME in the script first")
            sys.exit(1)
        
        query = " ".join(sys.argv[1:])
        results = query_similar_emails(query, INDEX_ENDPOINT_NAME, num_neighbors=5)
        display_results(results)
    else:
        main()


