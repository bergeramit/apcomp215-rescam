## Vertex AI Vector Search Setup Guide

Complete guide for setting up production-grade RAG with Vertex AI

---

## 🎯 **Overview**

You're using **Vertex AI Vector Search** (formerly Matching Engine) - Google Cloud's managed vector database service. This is production-ready and perfect for an MLOps course!

**What we're building:**
- Generate embeddings for 200+ phishing/legitimate emails
- Store in Vertex AI Vector Search (cloud-based, scalable)
- Query for similar emails (RAG retrieval)
- Use for phishing detection

---

## 📋 **Prerequisites**

✅ GCP project with billing enabled (`1097076476714`)  
✅ Vertex AI API enabled  
✅ GCS bucket (`rescam-dataset-bucket`)  
✅ Authenticated with `hprice@g.harvard.edu`  

---

## 🚀 **Step-by-Step Setup**

### **Step 1: Generate & Upload Embeddings (5 minutes)**

```bash
# Rebuild Docker with new dependencies
cd /Users/harryprice/AC215/phish/apcomp215-rescam/src/datapipeline
docker build -t preprocess-data -f Dockerfile .

# Run preprocessing
./docker-shell.sh
python3 preprocess_rag.py
```

**This will:**
- Download emails from `user_emails/` folder in GCS
- Generate 384-dim embeddings using sentence-transformers
- Upload embeddings to GCS at:
  ```
  gs://rescam-dataset-bucket/vertex_ai_embeddings/embeddings_for_vertex_ai.jsonl
  ```

---

### **Step 2: Enable Vertex AI API (1 minute)**

```bash
# Inside container or your terminal:
gcloud services enable aiplatform.googleapis.com --project=1097076476714
```

Or visit: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com

---

### **Step 3: Create Vector Search Index (Manual - 30-40 minutes)**

1. **Go to Vertex AI Console:**
   https://console.cloud.google.com/vertex-ai/matching-engine/indexes?project=1097076476714

2. **Click "CREATE INDEX"**

3. **Configure:**
   - **Name:** `phishing-email-index`
   - **Region:** `us-central1`
   - **Embedding dimension:** `384`
   - **Input data location:** `gs://rescam-dataset-bucket/vertex_ai_embeddings/`
   - **Algorithm:** Tree-AH (recommended for <100K vectors)
   - **Approximate neighbors:** `10`
   - **Distance measure:** `DOT_PRODUCT_DISTANCE` or `COSINE_DISTANCE`

4. **Click "CREATE"**

5. **Wait 30-40 minutes** for index to build
   - Status will show "Creating" → "Ready"
   - You'll get an email when done

---

### **Step 4: Create Index Endpoint (5 minutes)**

1. **Go to Index Endpoints:**
   https://console.cloud.google.com/vertex-ai/matching-engine/index-endpoints?project=1097076476714

2. **Click "CREATE ENDPOINT"**

3. **Configure:**
   - **Name:** `phishing-email-endpoint`
   - **Region:** `us-central1` (MUST match index region)
   - **Network:** Default (or leave as public)

4. **Click "CREATE"**

---

### **Step 5: Deploy Index to Endpoint (10-20 minutes)**

1. **Go back to your Index:**
   https://console.cloud.google.com/vertex-ai/matching-engine/indexes?project=1097076476714

2. **Click on** `phishing-email-index`

3. **Click "DEPLOY INDEX"**

4. **Configure Deployment:**
   - **Endpoint:** Select `phishing-email-endpoint`
   - **Deployed index ID:** `phishing_emails_deployed`
   - **Machine type:** `e2-standard-2` (cheapest option)
   - **Min replica count:** `1`
   - **Max replica count:** `1`

5. **Click "DEPLOY"**

6. **Wait 10-20 minutes** for deployment

---

### **Step 6: Test Queries**

Once deployed, update `query_vertex_ai.py`:

```python
# Get endpoint resource name from console, format:
INDEX_ENDPOINT_NAME = "projects/1097076476714/locations/us-central1/indexEndpoints/YOUR_ENDPOINT_ID"
```

Then run:

```bash
# Inside Docker container
python3 query_vertex_ai.py

# Or custom query:
python3 query_vertex_ai.py click here to verify your account
```

---

## 💰 **Cost Breakdown**

**One-time costs:**
- Index creation: ~$0.10 (one time)
- Index deployment: ~$0.05 (one time)

**Ongoing costs:**
- e2-standard-2 (1 replica): **~$0.10/hour = $72/month**
  - BUT: Can scale to 0 when not in use!
  - For development: Run ~10 hours total = **~$1**

**Storage:**
- GCS storage (embeddings): < $0.01/month
- Index storage: ~$0.50/month for 200 emails

**Queries:**
- First 1M queries/month: FREE
- After that: $0.50 per 1M queries

**Estimated total for course project: $5-15**

---

## 🛑 **How to Stop Costs**

### **Option 1: Undeploy Index (Keeps index, stops compute)**

```bash
# Via console: Go to endpoint → Click "UNDEPLOY"
# Cost drops to ~$0.50/month (just storage)
```

### **Option 2: Delete Everything**

```bash
# Delete endpoint
# Delete index
# Cost: $0
# Can rebuild from embeddings in GCS
```

---

## 🔧 **Troubleshooting**

### **"Index creation failed"**
- Check that GCS path is correct
- Verify JSONL file is properly formatted
- Ensure dimensions match (384)

### **"Permission denied"**
- Verify Vertex AI API is enabled
- Check IAM permissions for your account
- May need: Vertex AI User, Storage Object Viewer

### **"Endpoint not found"**
- Wait for deployment to complete (can take 20 min)
- Check region matches (us-central1)
- Verify endpoint ID is correct

### **"Query returns no results"**
- Check deployed_index_id matches ("phishing_emails_deployed")
- Verify embeddings were uploaded correctly
- Try different query text

---

## 📊 **Data Flow**

```
1. Emails CSV (GCS: user_emails/)
   ↓
2. preprocess_rag.py
   ↓
3. Embeddings JSONL (GCS: vertex_ai_embeddings/)
   ↓
4. Vertex AI Index (30-40 min build)
   ↓
5. Deploy to Endpoint (10-20 min)
   ↓
6. Query with query_vertex_ai.py
```

---

## ✅ **Verification Checklist**

Before your meeting:

- [ ] Vertex AI API enabled
- [ ] Embeddings uploaded to GCS
- [ ] Index created and shows "Ready"
- [ ] Endpoint created
- [ ] Index deployed to endpoint
- [ ] Can query and get results

---

## 🎓 **For Your MLOps Course**

**What this demonstrates:**
- ✅ Production-grade vector search (not just local dev)
- ✅ Cloud-native architecture
- ✅ Scalable infrastructure
- ✅ Proper ML deployment patterns
- ✅ Cost-aware engineering

**For your presentation/demo:**
- Show the Vertex AI console with your deployed index
- Demonstrate real-time queries
- Explain why Vertex AI vs local solutions
- Discuss scaling and cost trade-offs

---

## 🚀 **Next Steps After Setup**

1. **Build phishing classifier** using the retrieval results
2. **Integrate with LLM** (Vertex AI PaLM/Gemini) for classification
3. **Create API** to serve predictions
4. **Add monitoring** (Vertex AI Model Monitoring)
5. **CI/CD pipeline** for updating embeddings

---

## 📞 **Getting Help**

- **Vertex AI Docs:** https://cloud.google.com/vertex-ai/docs/matching-engine
- **Quotas:** https://console.cloud.google.com/iam-admin/quotas
- **Support:** GCP Console → Support

**Questions for Amit:**
- Do we have education credits to cover costs?
- Should we set budget alerts?
- Plan for scaling beyond 200 emails?


