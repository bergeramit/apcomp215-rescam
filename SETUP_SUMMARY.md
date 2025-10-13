# Rescam Project - Setup Summary

**Date:** October 13, 2025  
**Team:** Amit Berger, Harry Price  
**Course:** AC215 - MLOps/LLMOps

---

## ✅ Current Status

### **Environment Setup**
- ✅ Docker containerized development environment
- ✅ Google Cloud Storage integration (2 buckets)
- ✅ Vertex AI Vector Search configured
- ✅ Python 3.12 with uv dependency management

### **Data Pipeline (Complete)**
- ✅ `dataloader.py` - GCS upload/download
- ✅ `preprocess_clean.py` - Email data cleaning
- ✅ `generate_fake_emails.py` - Test data generation
- ✅ Fake dataset: 200 emails (100 phishing, 100 legitimate)

### **RAG Pipeline (Complete)**
- ✅ `preprocess_rag.py` - Embedding generation & upload
- ✅ Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- ✅ Quality tested: Phishing similarity 0.58, Category separation 0.24
- ✅ Embeddings uploaded to GCS
- ⏳ Vertex AI index building (30-40 min)

---

## 📊 GCS Buckets

### **rescam-dataset-bucket** (multi-region US)
```
├── raw-datasets/          # Original email CSVs
├── processed-dataset/     # Cleaned parquet files
└── user_emails/          # Test fake emails
```

### **rescam-rag-bucket** (us-central1)
```
└── vertex_ai_embeddings/
    ├── embeddings_for_vertex_ai.jsonl  # 200 email embeddings (384 dims)
    └── email_metadata.parquet          # Email metadata
```

---

## 🔧 How to Run

### **1. Start Development Environment**
```bash
cd /Users/harryprice/AC215/phish/apcomp215-rescam/src/datapipeline
./docker-shell.sh
```

### **2. Generate Test Data**
```bash
# Outside container
python3 generate_fake_emails.py

# Inside container
python3 upload_fake_data.py
```

### **3. Run Data Cleaning Pipeline**
```bash
# Inside container
python3 preprocess_clean.py
```

### **4. Run RAG Preprocessing**
```bash
# Inside container
python3 preprocess_rag.py
```

### **5. Test Embeddings Locally**
```bash
# Inside container
python3 test_embeddings_local.py
```

### **6. Query Vertex AI (After deployment)**
```bash
# Inside container
python3 query_vertex_ai.py
```

---

## 📈 Test Results

**Embedding Quality (from test_embeddings_local.py):**
- Phishing-to-phishing similarity: **0.58** ✅
- Legitimate-to-legitimate similarity: **0.40** ✅  
- Cross-category similarity: **0.24** ✅ (well separated)
- Search accuracy: **100%** (top 5 results all correct category)

---

## 🚀 Next Steps

### **Immediate (Waiting for index)**
- [ ] Index builds (~30-40 min)
- [ ] Deploy index to endpoint (~10-20 min)
- [ ] Test queries with `query_vertex_ai.py`

### **Milestone 2**
- [ ] Build phishing detection logic (retrieval + LLM)
- [ ] Integrate with Vertex AI Gemini
- [ ] Create inference pipeline
- [ ] Test with real email data

### **Future Milestones**
- [ ] Build REST API for predictions
- [ ] Create web interface
- [ ] Add monitoring/logging
- [ ] CI/CD pipeline
- [ ] Production deployment

---

## 💰 Cost Awareness

**Current costs (approximate):**
- GCS storage: ~$0.01/month
- Vertex AI index (when deployed): ~$0.10/hour = $2.40/day
- Can undeploy when not in use to save costs

**Recommendation:** Undeploy index when not actively developing

---

## 🐛 Known Issues

- Docker PATH not configured by default (need to add manually)
- gcloud CLI quota project warning (can ignore for now)
- Minor import error in test_embeddings_local.py (doesn't affect functionality)

---

## 📚 Key Files

| File | Purpose | Status |
|------|---------|--------|
| `Dockerfile` | Container definition | ✅ Working |
| `pyproject.toml` | Dependencies | ✅ Updated |
| `dataloader.py` | GCS operations | ✅ Working |
| `preprocess_clean.py` | Data cleaning | ✅ Working |
| `preprocess_rag.py` | RAG preprocessing | ✅ Complete |
| `test_embeddings_local.py` | Local testing | ✅ Working |
| `query_vertex_ai.py` | Query deployed index | ⏳ Ready for deployment |
| `generate_fake_emails.py` | Test data generator | ✅ Working |

---

## 🎓 Technical Stack

**Infrastructure:**
- Docker containerization
- Google Cloud Platform (GCP)
- Vertex AI Vector Search

**ML/AI:**
- sentence-transformers (all-MiniLM-L6-v2)
- 384-dimensional embeddings
- Cosine similarity search

**Data:**
- Pandas for data manipulation
- Parquet for efficient storage
- CSV for raw input

**Dependencies:**
- Python 3.12
- uv for package management
- google-cloud-storage
- google-cloud-aiplatform
- torch, sentence-transformers

---

**Last Updated:** October 13, 2025

