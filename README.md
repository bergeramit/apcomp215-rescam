# Rescam - Phishing Email Detection with RAG

Rescam is a phishing email detection system that uses Retrieval-Augmented Generation (RAG) to classify emails as benign, spam, scam, or suspicious. The system combines Vertex AI Vector Search for semantic similarity matching with Google's Gemini model for intelligent classification based on retrieved context.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Data Pipeline](#data-pipeline)
- [RAG Model Design](#rag-model-design)
- [Environment Setup](#environment-setup)
- [Docker Setup](#docker-setup)
- [Usage Instructions](#usage-instructions)
- [Project Structure](#project-structure)

## 🏗️ Architecture Overview

The Rescam system consists of two main components:

1. **Data Pipeline** (`src/datapipeline/`): Processes raw email datasets, creates unified datasets, and builds a RAG index using Vertex AI Vector Search
2. **Models** (`src/models/`): Uses the RAG index to classify new emails using a Gemini-based classifier

### Data Flow

```
Raw Email Data (CSV files)
    ↓
[preprocess_clean.py] → Unified Dataset (Parquet) → GCS Bucket
    ↓
[preprocess_rag.py] → Embeddings → Vertex AI Vector Search Index
    ↓
[model_rag.py] → Query RAG Index → Classify Email → JSON Result
```

## 🔄 Data Pipeline

The data pipeline consists of two main preprocessing scripts:

### 1. `preprocess_clean.py`

**Purpose**: Accesses the GCP bucket, downloads raw email datasets, and creates a unified, cleaned dataset.

**What it does**:
- Downloads raw email CSV files from GCP bucket using `dataloader.py`
- Parses and cleans email data (sender, receiver, date, subject, body, labels, URLs)
- Filters and validates email records (ensures labels are 0 or 1)
- Combines all raw datasets into a single unified dataset
- Saves cleaned data as Parquet format (compressed, efficient for tabular data)
- Uploads the cleaned dataset back to GCS bucket

**Key Features**:
- Handles large CSV files with extended field size limits
- Preserves email metadata (sender, subject, date, URLs, spam flags)
- Tracks source database for each email
- Uses Parquet format for efficient storage and querying

### 2. `preprocess_rag.py`

**Purpose**: Creates the Vertex AI RAG (Retrieval-Augmented Generation) index by generating embeddings for all emails and indexing them in Vertex AI Vector Search.

**What it does**:
- Downloads cleaned email dataset from GCS bucket
- Generates embeddings for email content using `sentence-transformers` (all-MiniLM-L6-v2 model, 384 dimensions)
- Formats embeddings in Vertex AI-compatible JSONL format
- Uploads embeddings to GCS bucket for Vertex AI Vector Search
- Provides instructions for creating and deploying the Vertex AI index

**Technical Details**:
- **Embedding Model**: `all-MiniLM-L6-v2` (384-dimensional vectors)
- **Storage Format**: JSONL (one embedding per line with ID, embedding vector, and optional metadata)
- **Bucket Location**: `gs://rescam-dataset-bucket/vertex_ai_embeddings/`
- **Index Configuration**: Tree-AH algorithm for approximate nearest neighbor search

**Helper Files**:
- `query_vertex_ai.py`: Tests RAG retrieval by querying the Vertex AI index
- `upload_fake_data.py`: Utility for uploading test data to GCS
- `generate_fake_emails.py`: Generates synthetic email data for testing
- `dataloader.py`: Helper module for GCS bucket operations and file management

## 🤖 RAG Model Design

### `model_rag.py`

**Purpose**: Classifies emails using RAG-enabled generative AI.

**How it works**:

1. **Email Retrieval**: 
   - Reads email content from GCS bucket
   - Generates embedding for the email using the same sentence transformer model
   - Queries Vertex AI Vector Search to find similar emails (k=5 nearest neighbors)
   - Retrieves email metadata (sender, subject, labels) from local parquet file

2. **Context Building**:
   - Constructs RAG context string from retrieved similar emails
   - Includes distance scores, sender information, subjects, and labels
   - Formats context for inclusion in the classification prompt

3. **Classification**:
   - Uses Google's Gemini 2.5 Flash Lite model for classification
   - Provides comprehensive instruction prompt with:
     - Classification categories (benign, spam, scam, suspicious)
     - Heuristics for detection (sender identity, lookalike domains, urgent language, etc.)
     - Expected output format (JSON with classification, confidence, reasons, indicators)
   - Returns structured JSON classification result

**Output Format**:
```json
{
  "classification": "benign | spam | scam | suspicious",
  "confidence": 0.0-1.0,
  "primary_reason": "Evidence summary",
  "indicators": ["list", "of", "detected", "indicators"],
  "evidence": [
    {"source": "current_email", "quote": "..."},
    {"source": "rag", "quote": "..."}
  ],
  "parsed": {
    "sender_display": "...",
    "sender_email": "...",
    "from_domain": "...",
    "reply_to": "...",
    "links": ["..."],
    "attachments": ["..."]
  },
  "recommended_action": "allow | quarantine | warn_user | block_sender | report_phishing"
}
```

**Default Arguments**:
- Project ID: `1097076476714`
- Location: `us-east1`
- Index Endpoint ID: `3044332193032699904`
- Deployed Index ID: `phishing_emails_deployed_1760372787396`
- GCS Bucket: `rescam-dataset-bucket`
- Default email file: `example_last_email.txt`

## 🔧 Environment Setup

### Prerequisites

- Python 3.12+
- Google Cloud Platform account with billing enabled
- GCP Project ID: `1097076476714`
- Docker and Docker Compose installed
- Google Cloud SDK (`gcloud`) installed and authenticated

### GCP Authentication

1. **Install Google Cloud SDK** (if not already installed):
   ```bash
   # macOS
   brew install google-cloud-sdk
   ```

2. **Authenticate with GCP**:
   ```bash
   gcloud init
   gcloud auth application-default login
   gcloud config set project 1097076476714
   gcloud auth application-default set-quota-project 1097076476714
   ```

   This creates authentication files in:
   - `~/.config/gcloud/application_default_credentials.json`
   - `~/.config/gcloud/config.yaml`

3. **Copy credentials to project** (for Docker containers):
   ```bash
   mkdir -p src/datapipeline/secrets src/models/secrets
   cp ~/.config/gcloud/application_default_credentials.json src/datapipeline/secrets/
   cp ~/.config/gcloud/application_default_credentials.json src/models/secrets/
   ```

### Enable Required APIs

Enable the following Google Cloud APIs:

```bash
gcloud services enable aiplatform.googleapis.com --project=1097076476714
gcloud services enable storage-api.googleapis.com --project=1097076476714
```

Or enable via [GCP Console](https://console.cloud.google.com/apis/library)

## 🐳 Docker Setup

The project uses Docker for isolated, reproducible environments. Each component has its own Dockerfile, and a centralized `docker-compose.yml` manages both services.

### Docker Structure

- **`src/datapipeline/Dockerfile`**: Data pipeline container
  - Base: `python:3.12-slim-bookworm`
  - Uses `uv` for dependency management
  - Includes all preprocessing scripts and helpers
  - Mounts GCP credentials

- **`src/models/Dockerfile`**: Model inference container
  - Base: `python:3.12-slim-bookworm`
  - Uses `uv` for dependency management
  - Includes model scripts (`model_rag.py`, `train_model.py`, `infer_model.py`)
  - Mounts GCP credentials

- **`docker-compose.yml`**: Centralized orchestration
  - Defines both `datapipeline` and `models` services
  - Configures volumes for secrets
  - Sets default commands for each service
  - Environment variables for GCP authentication

### Building Docker Images

**Using Docker Compose** (Recommended):
```bash
# Build both containers
docker-compose build

# Build specific service
docker-compose build datapipeline
docker-compose build models
```

**Using individual Dockerfiles**:
```bash
# Data pipeline
cd src/datapipeline
docker build -t preprocess-data -f Dockerfile .

# Models
cd src/models
docker build -t ml-model -f Dockerfile .
```

### Docker Compose Configuration

The `docker-compose.yml` file is pre-configured with default commands:

- **datapipeline service**: Automatically runs `preprocess_clean.py` followed by `preprocess_rag.py`
- **models service**: Automatically runs `model_rag.py` with default arguments

Both services:
- Mount `./secrets` directory for GCP credentials (read-only)
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Enable Python unbuffered output for real-time logs

## 📝 Usage Instructions

### Quick Start with Docker Compose

The easiest way to run the entire pipeline:

```bash
# 1. Ensure credentials are in place
cp ~/.config/gcloud/application_default_credentials.json src/datapipeline/secrets/
cp ~/.config/gcloud/application_default_credentials.json src/models/secrets/

# 2. Build and run data pipeline (cleans data and creates RAG index)
docker-compose up datapipeline

# 3. After RAG index is created and deployed, run classification
docker-compose up models
```

### Detailed Workflow

#### Step 1: Clean and Prepare Data

```bash
# Using docker-compose
docker-compose up datapipeline

# Or manually
cd src/datapipeline
docker build -t preprocess-data -f Dockerfile .
docker run --rm -it \
  -v $(pwd)/secrets:/home/app/.config/gcloud:ro \
  preprocess-data bash

# Inside container
source /home/app/.venv/bin/activate
python preprocess_clean.py
```

**What happens**:
- Downloads raw email CSV files from GCS bucket
- Creates unified `cleaned_dataset.parquet`
- Uploads cleaned dataset back to GCS

#### Step 2: Create RAG Index

```bash
# Using docker-compose (runs after preprocess_clean.py)
docker-compose up datapipeline

# Or manually inside the container
python preprocess_rag.py
```

**What happens**:
- Downloads cleaned dataset from GCS
- Generates embeddings for all emails
- Uploads embeddings to `gs://rescam-dataset-bucket/vertex_ai_embeddings/`

**Next Steps** (Manual in GCP Console):
1. Create Vertex AI Vector Search Index (see `src/datapipeline/VERTEX_AI_SETUP.md`)
2. Create Index Endpoint
3. Deploy index to endpoint
4. Note the endpoint ID and deployed index ID

#### Step 3: Test RAG Retrieval (Optional)

```bash
cd src/datapipeline
docker-compose run --rm datapipeline bash -c "source /home/app/.venv/bin/activate && python query_vertex_ai.py"
```

#### Step 4: Classify Emails

```bash
# Using docker-compose (uses default arguments)
docker-compose up models

# Or with custom arguments
docker-compose run --rm models bash -c \
  "source /home/app/.venv/bin/activate && \
   python model_rag.py \
   --project_id 1097076476714 \
   --index_endpoint_id YOUR_ENDPOINT_ID \
   --deployed_index_id YOUR_DEPLOYED_INDEX_ID \
   --gcs_bucket_name rescam-dataset-bucket \
   --gcs_file_name example_last_email.txt"
```

### Alternative: Interactive Shell Mode

If you need to run custom commands or debug:

```bash
# Data pipeline interactive shell
docker-compose run --rm datapipeline

# Models interactive shell
docker-compose run --rm models

# Inside container, activate venv and run commands
source /home/app/.venv/bin/activate
python your_script.py
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f datapipeline
docker-compose logs -f models
```

### Stop Containers

```bash
# Stop and remove containers
docker-compose down

# Stop but keep containers
docker-compose stop
```

## 📁 Project Structure

```
AC215_rescam/
├── docker-compose.yml              # Centralized Docker orchestration
├── DOCKER_COMPOSE_GUIDE.md         # Detailed Docker Compose usage guide
├── README.md                        # This file
├── reports/
│   └── Journal.md                  # Development journal
├── src/
│   ├── datapipeline/               # Data preprocessing and RAG index creation
│   │   ├── Dockerfile
│   │   ├── docker-shell.sh
│   │   ├── pyproject.toml           # Dependencies
│   │   ├── preprocess_clean.py      # Clean and unify raw datasets
│   │   ├── preprocess_rag.py       # Create Vertex AI RAG index
│   │   ├── query_vertex_ai.py      # Test RAG retrieval
│   │   ├── dataloader.py           # GCS bucket helper
│   │   ├── upload_fake_data.py     # Test data uploader
│   │   ├── generate_fake_emails.py # Synthetic data generator
│   │   ├── test_embeddings_local.py
│   │   ├── VERTEX_AI_SETUP.md      # Detailed Vertex AI setup guide
│   │   └── secrets/                # GCP credentials (git-ignored)
│   │       └── application_default_credentials.json
│   └── models/                      # Email classification models
│       ├── Dockerfile
│       ├── docker-shell.sh
│       ├── pyproject.toml           # Dependencies
│       ├── model_rag.py             # RAG-based email classifier
│       ├── train_model.py           # Model training (if needed)
│       ├── infer_model.py           # Inference utilities
│       └── secrets/                 # GCP credentials (git-ignored)
│           └── application_default_credentials.json
```

## 🔒 Security Notes

**Current Setup (Development)**:
- Credentials are copied to `secrets/` directory and mounted into containers
- Credentials are git-ignored for security

**Production Recommendations** (from Journal.md):
1. **Service Account Keys**: Create a dedicated service account with minimal permissions
2. **Environment Variables**: Use environment variables instead of file mounting
3. **Workload Identity**: Use Google Cloud Run or Kubernetes with Workload Identity (most secure)

For more details on secure credential management, see `reports/Journal.md`.

## 📚 Additional Documentation

- **`DOCKER_COMPOSE_GUIDE.md`**: Comprehensive guide on using Docker Compose
- **`src/datapipeline/VERTEX_AI_SETUP.md`**: Step-by-step Vertex AI Vector Search setup
- **`src/datapipeline/TESTING_GUIDE.md`**: Testing procedures and examples
- **`reports/Journal.md`**: Development process and decisions

## 🚀 Next Steps

1. **Complete Vertex AI Setup**: Follow `src/datapipeline/VERTEX_AI_SETUP.md` to create and deploy the index
2. **Upload Test Emails**: Use `upload_fake_data.py` or upload emails directly to GCS bucket
3. **Test Classification**: Run `model_rag.py` with your deployed index
4. **Production Deployment**: Consider using Cloud Run or Kubernetes for production deployment

## 💰 Cost Considerations

- **Vertex AI Vector Search**: ~$0.10/hour for e2-standard-2 instance (~$72/month if running 24/7)
- **GCS Storage**: Minimal cost for dataset storage
- **Gemini API**: Pay-per-use pricing
- **Recommendation**: Undeploy index when not in use to reduce costs to ~$0.50/month (storage only)

For detailed cost breakdown, see `src/datapipeline/VERTEX_AI_SETUP.md`.

## 🆘 Troubleshooting

### Common Issues

**"Permission denied" when accessing GCS**:
- Verify credentials are in `secrets/` directory
- Check that `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
- Ensure GCS bucket permissions are configured

**"Index endpoint not found"**:
- Verify Vertex AI index is deployed to endpoint
- Check endpoint ID and deployed index ID match your configuration
- Wait for deployment to complete (can take 20+ minutes)

**"No similar emails found" in RAG retrieval**:
- Verify `email_metadata.parquet` exists in working directory
- Check that embeddings were uploaded correctly
- Ensure index is ready and deployed

**Container won't start**:
- Check Docker logs: `docker-compose logs`
- Verify credentials file exists in `secrets/` directory
- Rebuild containers: `docker-compose build --no-cache`

For more troubleshooting tips, see `src/datapipeline/VERTEX_AI_SETUP.md`.
