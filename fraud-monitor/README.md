# Fraud Monitor

A serverless transactional anomaly detection pipeline that combines heuristic rule checks with an **Isolation Forest** machine learning model capable of **dynamic online retraining** directly inside AWS Lambda.

---

## 🕵️‍♂️ How It Works

1. **Ingestion Trigger:** A batch CSV containing credit card transactions is uploaded directly to the S3 bucket (`TransactionBatchesBucket`).
2. **Lambda Processor (`src/handler.py`):**
   - Wipes historical findings with DynamoDB pagination to provide clean batch reporting.
   - Streams the CSV file to track byte progress and write updates to DynamoDB under `JOB_PROGRESS`.
   - **Dynamic Online Retraining:** If PCA features (`V1`–`V28`) are present in the batch, `retrain_model()` in `src/model/inference.py` fits a fresh `IsolationForest` on the uploaded distribution, persists it to `/tmp/`, and hot-reloads it in memory.
3. **Dual-Layer Evaluation:**
   - **Rule Engine (`src/rules/engine.py`):** Flags high transaction amounts (>$1,000), high-risk merchants (`crypto_exchange`, `jewelry`, `casino`, `wire_transfer`, `electronics_wholesale`), and velocity spikes (>5 recent transactions).
   - **AI Anomaly Detection (`src/model/inference.py`):** Calculates an explainable Risk Score (0.0 to 1.0) and isolates top contributing PCA features.
4. **Findings & Alerts:**
   - Evaluated records with risk scores $\ge 0.40$ or triggered rules are written to DynamoDB `Findings` with chronological sort keys.
   - Dual-flagged findings (both AI anomaly and rule triggers) are assigned **CRITICAL** severity and published immediately to the **SNS Alert Topic**.

---

## 🤖 Why Isolation Forest & Dynamic Online Learning?

- **Unsupervised Anomaly Isolation:** Normal transactions cluster closely in feature space, while fraudulent patterns partition with shallow tree depths. Isolation Forest isolates anomalies without requiring imbalanced supervised labels.
- **Dynamic Online Retraining:** Rather than relying on a static offline model that suffers from distribution drift, the Lambda automatically fits to the specific variance and column scale of the uploaded portfolio before scoring.
- **Explainability:** When an anomaly is detected, the top 3 feature deviations are ranked and saved alongside the finding, providing investigators with clear context behind the AI score.

---

## 💻 Local Setup & Testing

```bash
# Navigate to fraud-monitor directory
cd fraud-monitor

# Optional: Train a local reference model
python src/model/prep_data.py
python src/model/train.py

# Test invocation with SAM Local
sam local invoke FraudBatchProcessorFunction -e events/s3_upload_event.json
```

---

## 🚀 Deployment

```bash
sam deploy --resolve-s3 --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

