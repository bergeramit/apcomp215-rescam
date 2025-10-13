# Testing Guide - Fake Email Dataset

## Quick Start: Test the Full Pipeline

### Step 1: Generate Fake Emails

```bash
# Outside container (on your laptop)
cd /Users/harryprice/AC215/phish/apcomp215-rescam/src/datapipeline

# Create raw-datasets folder if it doesn't exist
mkdir -p raw-datasets

# Generate fake emails
python3 generate_fake_emails.py
```

This creates: `raw-datasets/fake_phishing_dataset.csv` with 200 emails (100 legit, 100 phishing)

---

### Step 2: Upload to GCS (Optional - for full pipeline test)

```bash
# Inside Docker container
./docker-shell.sh

# Then inside the container:
python3 upload_fake_data.py
```

**OR test locally without GCS (faster for development):**

Just skip this step - the fake CSV is already in `raw-datasets/` locally!

---

### Step 3: Test the Cleaning Pipeline

```bash
# Inside Docker container
python3 preprocess_clean.py
```

This will:
- Find your fake CSV in `raw-datasets/`
- Clean it (extract sender, subject, body, label, URLs)
- Save to `processed-dataset/cleaned_dataset.parquet`

---

### Step 4: Verify It Worked

```bash
# Inside container, open Python:
python3

# Then:
import pandas as pd
df = pd.read_parquet('processed-dataset/cleaned_dataset.parquet')
print(f"Total emails: {len(df)}")
print(f"Legit emails: {len(df[df['label']==0])}")
print(f"Phishing emails: {len(df[df['label']==1])}")
print("\nFirst few rows:")
print(df.head())
```

---

## What the Fake Data Looks Like

### CSV Format (matches your schema):

```csv
sender,receiver,date,subject,body,label,urls
notifications@github.com,user@company.com,2024-10-01 14:23:00,"Pull request merged","Your PR has been merged",0,https://github.com
security@paypa1.com,john@email.com,2024-09-15 09:00:00,"URGENT: Verify account","Click here: http://evil.com",1,http://evil.com
```

### Fields:
- **sender**: Email sender address
- **receiver**: Email recipient
- **date**: Timestamp
- **subject**: Email subject line
- **body**: Email body text
- **label**: 0 = legitimate, 1 = phishing
- **urls**: Links in the email (if any)

---

## Customizing the Fake Data

Edit `generate_fake_emails.py` to:

```python
# Generate more/fewer emails
generate_dataset(
    num_legit=500,      # More legitimate emails
    num_phishing=500,   # More phishing emails
    filename="raw-datasets/my_custom_dataset.csv"
)
```

Add your own fake email templates by editing the lists:
- `LEGIT_SENDERS` / `PHISHING_SENDERS`
- `LEGIT_SUBJECTS` / `PHISHING_SUBJECTS`
- `LEGIT_BODIES` / `PHISHING_BODIES`

---

## Testing RAG Preprocessing (Your Work)

Once you build `preprocess_rag.py`:

```bash
# Load the cleaned parquet
# Generate embeddings
# Test retrieval
python3 preprocess_rag.py
```

The fake data gives you realistic test cases without needing real email access!

---

## Why This Approach?

✅ **Fast**: Generate 1000s of emails in seconds  
✅ **Realistic**: Looks like real phishing vs legitimate emails  
✅ **Safe**: No privacy concerns with fake data  
✅ **Flexible**: Easy to customize for testing edge cases  
✅ **Matches Schema**: Works with existing `dataloader.py` and `preprocess_clean.py`

---

## Next Steps

1. Generate fake data ✓
2. Test cleaning pipeline works ✓
3. Build RAG preprocessing on top of cleaned data
4. Later: Replace with real email data when ready


