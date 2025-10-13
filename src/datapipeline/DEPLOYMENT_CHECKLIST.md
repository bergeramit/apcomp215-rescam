# Vertex AI Deployment Checklist

Track your deployment progress here!

---

## ✅ Completed Steps

- [x] Generate embeddings (384 dims, 200 emails)
- [x] Upload to GCS (`gs://rescam-rag-bucket/vertex_ai_embeddings/`)
- [x] Create endpoint (`phishing-email-endpoint` in us-central1)
- [x] Create index (`phishing-email-index`)

---

## ⏳ In Progress

- [ ] **Index building** (Started: _____ | Expected completion: ~40 min)
  - Status page: https://console.cloud.google.com/vertex-ai/matching-engine/indexes?project=1097076476714
  - Check status regularly
  - Will show "Ready" when done

---

## 📋 Next Steps (After Index is Ready)

### **Step 1: Deploy Index to Endpoint**

1. Go to: https://console.cloud.google.com/vertex-ai/matching-engine/indexes?project=1097076476714
2. Click on `phishing-email-index`
3. Click **"DEPLOY TO ENDPOINT"**
4. Select endpoint: `phishing-email-endpoint`
5. Configure deployment:
   - **Deployed index ID:** `phishing_emails_deployed`
   - **Display name:** `Phishing Emails Index`
   - **Machine type:** `e2-standard-2`
   - **Min replica count:** `1`
   - **Max replica count:** `1`
   - **Auto-scaling disabled:** Yes (keep it simple)
6. Click **"DEPLOY"**
7. Wait 10-20 minutes

---

### **Step 2: Get Endpoint Resource Name**

After deployment completes:

1. Go to: https://console.cloud.google.com/vertex-ai/matching-engine/index-endpoints?project=1097076476714
2. Click on `phishing-email-endpoint`
3. Copy the **Resource name** (format: `projects/1097076476714/locations/us-central1/indexEndpoints/XXXXXXXXXX`)
4. Update `query_vertex_ai.py`:

```python
INDEX_ENDPOINT_NAME = "projects/1097076476714/locations/us-central1/indexEndpoints/YOUR_ENDPOINT_ID"
```

---

### **Step 3: Test Queries**

```bash
# Inside Docker container
./docker-shell.sh
python3 query_vertex_ai.py

# Or custom query:
python3 query_vertex_ai.py click here to verify your account now
```

**Expected output:**
```
🔍 Querying Vertex AI Vector Search...
   Query: "click here to verify your account now"
   
✅ Found 5 results

📧 Result #1
   Distance: 0.2341 (lower = more similar)
   Sender: security@paypa1.com
   Label: 🚨 PHISHING
   Subject: URGENT: Verify your account immediately
```

---

## 🎯 Success Criteria

You'll know it's working when:
- ✅ Index status shows "Ready"
- ✅ Deployment status shows "Deployed"
- ✅ Queries return relevant phishing emails
- ✅ Similar emails cluster together (low distance scores)

---

## 💰 Cost Tracking

**Deployment costs (when running):**
- e2-standard-2 (1 replica): ~$0.10/hour
- For development: Run only when testing
- **Remember to undeploy when done!**

**How to stop costs:**
1. Go to endpoint page
2. Click on deployed index
3. Click **"UNDEPLOY"**
4. Index remains available, can redeploy anytime

---

## 🐛 Troubleshooting

**If queries fail:**
- Check endpoint is "Deployed" (not just "Ready")
- Verify `deployed_index_id` matches (`phishing_emails_deployed`)
- Check endpoint resource name is correct
- Ensure you're using same embedding model (all-MiniLM-L6-v2)

**If results seem wrong:**
- Check distance scores (should be 0-1 for cosine)
- Verify metadata is present
- Test with known phishing queries

---

## ⏰ Timeline

| Task | Status | Time |
|------|--------|------|
| Generate embeddings | ✅ Done | 2 min |
| Upload to GCS | ✅ Done | 1 min |
| Create endpoint | ✅ Done | 2 min |
| Create index | ⏳ Building | 30-40 min |
| Deploy to endpoint | ⏸️ Waiting | 10-20 min |
| Test queries | ⏸️ Waiting | 2 min |

**Total time:** ~45-65 minutes from start to finish

---

**Next check-in:** _____ (write time to check if index is ready)

