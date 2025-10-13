# -*- coding: utf-8 -*-
"""This script classifies an email as spam or not spam using a RAG model.

It fetches an email from a GCS bucket, uses a pre-configured Vertex AI RAG
corpus to find similar emails, and prompts a generative model to classify it.
"""

import argparse
import logging

import vertexai
from google.cloud import storage
from vertexai.generative_models import GenerativeModel
from vertexai.preview.generative_models import Tool
from vertexai.preview.rag import RagCorpus

logging.basicConfig(level=logging.INFO)

INSTRUCTION_PROMPT = """
You are an intelligent email risk classifier.
You receive the **current email** (body and optional headers) and have access to a **retrieval-augmented context (RAG)** containing samples of this user’s previous emails.

---

## Objective

Classify the email as one of:

* **benign** — expected or legitimate message
* **spam** — unsolicited or irrelevant marketing/bulk message
* **scam** — deceptive or malicious message attempting to obtain money, credentials, or sensitive information
* **suspicious** — signals of risk present, but insufficient evidence for clear classification

Provide a **short, evidence-based rationale** explaining why you chose that label.

---

## What the RAG contains

The RAG includes past messages, both legitimate and malicious, with metadata such as:

* sender name and address
* domain
* subject lines
* message snippets or short summaries
* timestamp
* (optional) known labels like *spam*, *scam*, or *benign*

You can conceptually use this information to:

* Identify whether this sender or domain has appeared before
* Check if similar wording, tone, or formatting matches known spam/scam patterns
* See if similar messages were legitimate in the past
* Detect unusual senders, domains, or topics compared to the user’s historical communication

---

## Classification Heuristics

Consider:

* Sender identity and domain similarity to known contacts
* Lookalike domains or spoofing attempts
* Unusual reply-to addresses
* Urgent or threatening language
* Requests for payments, credentials, or MFA codes
* Suspicious attachments or links (e.g., shortened, IP-only, mismatched anchors)
* Thread hijacking or fake invoice/inquiry patterns
* DKIM/SPF/DMARC information if available
* Consistency with previous legitimate correspondence from the RAG

---

## Output Format

Return **only** a single JSON object in the following structure:

```json
{
  "classification": "benign | spam | scam | suspicious",
  "confidence": 0.0,
  "primary_reason": "≤40 words summarizing the decisive signals",
  "indicators": [
    "mismatched_sender",
    "lookalike_domain",
    "unknown_sender_no_history",
    "urgent_language",
    "payment_request",
    "credential_harvest",
    "attachment_risky",
    "link_shortener",
    "dkim_spf_dmarc_fail",
    "thread_hijack",
    "known_contact_match",
    "bulk_marketing_traits",
    "headers_missing",
    "rag_empty"
  ],
  "evidence": [
    {
      "source": "current_email",
      "quote": "short quote…"
    },
    {
      "source": "rag",
      "quote": "short quote or match summary…"
    }
  ],
  "parsed": {
    "sender_display": "…",
    "sender_email": "…",
    "from_domain": "…",
    "reply_to": "…",
    "links": ["list of extracted domains/URLs if any"],
    "attachments": ["names/extensions if any"],
    "headers_used": true
  },
  "recommended_action": "allow | quarantine | warn_user | block_sender | report_phishing"
}
```

---

## Inputs

```
CURRENT_EMAIL_BODY:
---
{email_content}
---
```

**Now:**
Use the email and relevant RAG context to infer risk, then output your classification and reasoning strictly in the JSON format above — no extra text or commentary.
"""

def read_email_from_gcs(bucket_name: str, file_name: str) -> str:
    """Reads the content of an email from a GCS bucket.

    Args:
        bucket_name: The name of the GCS bucket.
        file_name: The name of the file (email) in the bucket.

    Returns:
        The content of the email as a string.
    """
    logging.info(f"Reading email '{file_name}' from bucket '{bucket_name}'.")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        email_content = blob.download_as_text()
        return email_content
    except Exception as e:
        logging.error(f"Failed to read from GCS: {e}")
        raise

def classify_email_with_rag(
    project_id: str,
    location: str,
    rag_corpus_id: str,
    gcs_bucket_name: str,
    gcs_file_name: str,
) -> str:
    """Classifies an email using a RAG-enabled generative model.

    Args:
        project_id: Your Google Cloud project ID.
        location: The GCP region for your resources.
        rag_corpus_id: The ID of your Vertex AI RAGCorpus.
        gcs_bucket_name: The GCS bucket containing the email.
        gcs_file_name: The email file to classify.

    Returns:
        The classification result ('spam' or 'not spam').
    """
    # 1. Initialize Vertex AI
    logging.info(f"Initializing Vertex AI for project '{project_id}' in '{location}'.")
    vertexai.init(project=project_id, location=location)

    # 2. Read email content from GCS
    email_content = read_email_from_gcs(gcs_bucket_name, gcs_file_name)

    # 3. Configure the RAG tool
    rag_corpus = RagCorpus(
        name=f"projects/{project_id}/locations/{location}/ragCorpora/{rag_corpus_id}"
    )
    rag_tool = Tool.from_retrieval(
        retrieval=rag_corpus
    )

    # 4. Load the generative model
    model = GenerativeModel("gemini-1.5-flash-001", tools=[rag_tool])

    # 5. Construct the prompt and generate content
    prompt = INSTRUCTION_PROMPT.format(email_content=email_content)

    logging.info("Sending request to the generative model...")
    response = model.generate_content(prompt)

    classification = response.text.strip().lower()
    logging.info(f"Classification result: {classification}")

    return classification


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Classify an email as spam or not spam using a RAG model."
    )
    parser.add_argument("--project_id", required=True, help="Your Google Cloud project ID.")
    parser.add_argument(
        "--location",
        default="us-central1",
        help="The GCP region for your resources (e.g., 'us-central1').",
    )
    parser.add_argument(
        "--rag_corpus_id", required=True, help="The ID of your Vertex AI RAGCorpus."
    )
    parser.add_argument(
        "--bucket", required=True, help="The GCS bucket where the email is located."
    )
    parser.add_argument(
        "--file", required=True, help="The name of the email file in the GCS bucket."
    )

    args = parser.parse_args()

    result = classify_email_with_rag(
        project_id=args.project_id,
        location=args.location,
        rag_corpus_id=args.rag_corpus_id,
        gcs_bucket_name=args.bucket,
        gcs_file_name=args.file,
    )

    print(f"\nThe email '{args.file}' is classified as: {result}")