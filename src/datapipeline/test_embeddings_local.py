"""
Test embeddings locally without deploying to Vertex AI
Verify that embeddings are working properly
"""
import pandas as pd
import numpy as np
from preprocess_rag import download_user_emails_from_gcs, load_emails, prepare_text_for_embedding, generate_embeddings


def compute_similarity(emb1, emb2):
    """Compute cosine similarity between two embeddings"""
    from numpy.linalg import norm
    return np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))


def test_embedding_quality(df):
    """
    Test that embeddings make sense
    - Similar emails should have similar embeddings
    - Phishing vs legitimate should be somewhat different
    """
    print("\n" + "=" * 70)
    print("Testing Embedding Quality")
    print("=" * 70)
    
    # Convert embeddings to numpy array for easier math
    embeddings = np.array([emb for emb in df['embedding']])
    
    # Test 1: Phishing emails should be similar to each other
    print("\n📊 Test 1: Similarity within same category")
    phishing_emails = df[df['label'] == 1].head(10)
    legit_emails = df[df['label'] == 0].head(10)
    
    if len(phishing_emails) >= 2:
        phish_emb1 = np.array(phishing_emails.iloc[0]['embedding'])
        phish_emb2 = np.array(phishing_emails.iloc[1]['embedding'])
        phish_similarity = compute_similarity(phish_emb1, phish_emb2)
        
        print(f"   Phishing email 1: {phishing_emails.iloc[0]['subject'][:50]}")
        print(f"   Phishing email 2: {phishing_emails.iloc[1]['subject'][:50]}")
        print(f"   Similarity: {phish_similarity:.4f}")
        print(f"   {'✅ GOOD' if phish_similarity > 0.3 else '⚠️  LOW - might need better embeddings'}")
    
    if len(legit_emails) >= 2:
        legit_emb1 = np.array(legit_emails.iloc[0]['embedding'])
        legit_emb2 = np.array(legit_emails.iloc[1]['embedding'])
        legit_similarity = compute_similarity(legit_emb1, legit_emb2)
        
        print(f"\n   Legitimate email 1: {legit_emails.iloc[0]['subject'][:50]}")
        print(f"   Legitimate email 2: {legit_emails.iloc[1]['subject'][:50]}")
        print(f"   Similarity: {legit_similarity:.4f}")
        print(f"   {'✅ GOOD' if legit_similarity > 0.3 else '⚠️  LOW - might need better embeddings'}")
    
    # Test 2: Cross-category similarity
    print("\n📊 Test 2: Difference between categories")
    if len(phishing_emails) >= 1 and len(legit_emails) >= 1:
        cross_similarity = compute_similarity(phish_emb1, legit_emb1)
        print(f"   Phishing: {phishing_emails.iloc[0]['subject'][:50]}")
        print(f"   Legitimate: {legit_emails.iloc[0]['subject'][:50]}")
        print(f"   Similarity: {cross_similarity:.4f}")
        print(f"   {'✅ GOOD - Different enough' if cross_similarity < 0.7 else '⚠️  TOO SIMILAR - might have issues'}")
    
    # Test 3: Find most similar email to a query
    print("\n📊 Test 3: Similarity Search Test")
    query_text = "Click here to verify your account immediately"
    print(f"   Query: \"{query_text}\"")
    
    # Generate embedding for query (using same model)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_emb = model.encode([query_text])[0]
    
    # Find most similar emails
    similarities = [compute_similarity(query_emb, emb) for emb in embeddings]
    top_5_idx = np.argsort(similarities)[-5:][::-1]
    
    print(f"\n   Top 5 most similar emails:")
    for i, idx in enumerate(top_5_idx):
        row = df.iloc[idx]
        sim = similarities[idx]
        label = "🚨 PHISHING" if row['label'] == 1 else "✅ LEGITIMATE"
        print(f"\n   {i+1}. Similarity: {sim:.4f} | {label}")
        print(f"      Subject: {row['subject'][:60]}")
        print(f"      Snippet: {row['body'][:100]}...")
    
    # Test 4: Statistics
    print("\n📊 Test 4: Embedding Statistics")
    print(f"   Total embeddings: {len(embeddings)}")
    print(f"   Embedding dimension: {embeddings.shape[1]}")
    print(f"   Mean value: {embeddings.mean():.6f}")
    print(f"   Std deviation: {embeddings.std():.6f}")
    print(f"   Min value: {embeddings.min():.6f}")
    print(f"   Max value: {embeddings.max():.6f}")
    
    # Check for any zero/NaN embeddings
    zero_embeddings = np.sum(np.all(embeddings == 0, axis=1))
    nan_embeddings = np.sum(np.isnan(embeddings).any(axis=1))
    print(f"\n   Zero embeddings: {zero_embeddings} {'✅' if zero_embeddings == 0 else '❌'}")
    print(f"   NaN embeddings: {nan_embeddings} {'✅' if nan_embeddings == 0 else '❌'}")


def inspect_sample_data(df):
    """Show sample of processed data"""
    print("\n" + "=" * 70)
    print("Sample Data Inspection")
    print("=" * 70)
    
    print(f"\n📧 Total emails: {len(df)}")
    print(f"   Phishing: {len(df[df['label']==1])} ({len(df[df['label']==1])/len(df)*100:.1f}%)")
    print(f"   Legitimate: {len(df[df['label']==0])} ({len(df[df['label']==0])/len(df)*100:.1f}%)")
    
    if 'spam_flag' in df.columns:
        print(f"\n📮 Spam flags:")
        print(f"   Marked as spam: {len(df[df['spam_flag']==1])}")
        print(f"   Not marked as spam: {len(df[df['spam_flag']==0])}")
    
    print(f"\n📝 Text lengths:")
    text_lengths = df['combined_text'].str.len()
    print(f"   Average: {text_lengths.mean():.0f} characters")
    print(f"   Min: {text_lengths.min()}")
    print(f"   Max: {text_lengths.max()}")
    print(f"   {'⚠️  Some very long emails' if text_lengths.max() > 2000 else '✅ Reasonable lengths'}")
    
    # Show a few examples
    print("\n📋 Sample Emails:")
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        label = "🚨 PHISHING" if row['label'] == 1 else "✅ LEGITIMATE"
        print(f"\n   {i+1}. {label}")
        print(f"      From: {row['sender']}")
        print(f"      Subject: {row['subject'][:70]}")
        print(f"      Body: {row['body'][:100]}...")
        print(f"      Embedding: [{row['embedding'][0]:.4f}, {row['embedding'][1]:.4f}, ..., {row['embedding'][-1]:.4f}] ({len(row['embedding'])} dims)")


def save_embeddings_locally(df, output_path="local_embeddings.parquet"):
    """Save embeddings to local file for inspection"""
    print(f"\n💾 Saving embeddings locally to {output_path}...")
    df.to_parquet(output_path, index=False)
    print(f"✅ Saved {len(df)} emails with embeddings")
    print(f"   File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    return output_path


def main():
    """Run local embedding test"""
    import os
    
    print("=" * 70)
    print("Local Embedding Quality Test")
    print("=" * 70)
    print("\nThis will:")
    print("1. Download emails from GCS")
    print("2. Generate embeddings locally")
    print("3. Run quality tests")
    print("4. NOT upload to Vertex AI")
    print("=" * 70)
    
    # Step 1: Load data
    print("\n[1/4] Downloading emails...")
    files = download_user_emails_from_gcs()
    
    print("\n[2/4] Loading and preparing data...")
    df = load_emails(files)
    df = prepare_text_for_embedding(df)
    
    # Step 3: Generate embeddings
    print("\n[3/4] Generating embeddings...")
    df = generate_embeddings(df)
    
    # Step 4: Test quality
    print("\n[4/4] Testing embedding quality...")
    inspect_sample_data(df)
    test_embedding_quality(df)
    
    # Save locally
    output_path = save_embeddings_locally(df)
    
    print("\n" + "=" * 70)
    print("✅ Local Test Complete!")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  - Embeddings look good: Check similarity scores above")
    print(f"  - Saved to: {output_path}")
    print(f"  - Ready for Vertex AI when you're ready to deploy")
    print(f"\nNext steps:")
    print(f"  1. Review the quality tests above")
    print(f"  2. If embeddings look good, run: python3 preprocess_rag.py")
    print(f"  3. That will upload to GCS for Vertex AI deployment")
    

if __name__ == "__main__":
    main()


