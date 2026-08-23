with open('C:/Users/benny/.gemini/antigravity/brain/52042120-83fa-4969-a9f3-659b5874026d/walkthrough.md', 'a') as f:
    f.write('''

## Phase 7: Secure Frontend Uploads

We added a secure file upload component to the Fraud Monitor page. To protect the system from viruses, we utilized **S3 Pre-signed POST URLs**.

1. The frontend requests a "ticket" from the API (`GET /upload-url`).
2. The API uses `boto3` to generate a cryptographic ticket with strict conditions:
   - `Content-Type` must be `text/csv`.
   - File size must be between 1 byte and 5MB.
3. The frontend uses this ticket to upload the file directly to S3. If a malicious user attempts to upload an executable or a massive payload, S3 rejects it at the edge before it ever reaches our serverless architecture.
''')
