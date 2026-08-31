# API Layer

A lightweight, serverless REST API built with AWS API Gateway and a "Lambda Lith" Python handler (`src/app.py`). It mediates secure read access to the DynamoDB `Findings` table and generates presigned S3 upload tickets for the Next.js frontend dashboard.

---

## 🌐 Endpoints & Operations

| Method | Path | Description | Query Parameters / Body |
|---|---|---|---|
| `GET` | `/overview-data` | Aggregates all open findings by severity across both `COMPLIANCE` and `FRAUD` pipelines using paginated table scans. | None |
| `GET` | `/findings` | Returns the 50 most recent findings sorted chronologically. | `?type=FRAUD` or `?type=COMPLIANCE` (defaults to `COMPLIANCE`) |
| `GET` | `/findings/{id}` | Retrieves full audit detail for a specific finding. | `?type=FRAUD` or `?type=COMPLIANCE` |
| `GET` | `/processing-status/{job_id}` | Checks S3 batch streaming byte progress and completion state. | URL path parameter `job_id` |
| `POST` | `/upload-url` | Generates a secure S3 Presigned POST policy allowing direct in-browser upload of CSV batches up to 1GB. | Body: `{"filename": "transactions.csv"}` |
| `OPTIONS`| `/*` | CORS preflight handler responding with allowed origins, headers, and HTTP methods. | None |

---

## 🔒 Security & Data Serialization

- **Path Traversal Sanitization:** Filenames supplied to `/upload-url` are sanitized with `os.path.basename()` and constrained to `.csv` formats within the `uploads/` S3 prefix.
- **Recursive DynamoDB Deserialization:** The `clean_dynamo_item()` utility recursively unwraps DynamoDB typed attributes (`S`, `N`, `M`, `L`, `BOOL`, `NULL`) into clean JSON for frontend consumption.
- **Scan & Query Pagination:** Uses `ExclusiveStartKey` pagination loops to ensure complete dataset coverage beyond DynamoDB's default 1MB response limit.

---

## 🚀 Deployment

```bash
sam deploy --resolve-s3 --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

