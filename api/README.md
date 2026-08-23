# API Layer

Welcome to the API Layer! 🌐

Think of our DynamoDB database as a highly secure vault. Our future website isn't allowed to reach directly into the vault. Instead, the website will talk to this **API** (a digital teller). The API safely fetches the data from the vault and hands it back to the website.

## How it works

This folder uses AWS SAM to create two things:
1. **API Gateway**: This gives us a public URL (like `https://api.mybank.com`) that our website can talk to.
2. **Lambda Function (`src/app.py`)**: A simple Python script that acts as our "teller". 

To make it easy to read and learn from, we put all our logic into a single Python file (`app.py`). When a request comes in, the script acts like a traffic cop, checking the URL and deciding which helper function to run.

## The Commands (Endpoints)

Our API understands three commands:

1. `GET /findings?type=FRAUD`
   - Returns a list of the 50 most recent fraud alerts so the website can show them in a table.
2. `GET /findings/12345?type=FRAUD`
   - Returns the full details of a *single* specific alert so the website can show a detailed view.
3. `GET /stats/summary`
   - Counts up all our open alerts (e.g., "5 Critical Frauds") so the website can show dashboard summary cards at the top of the screen.

## Note on DynamoDB

DynamoDB returns data in a clunky format (e.g. `{"severity": {"S": "HIGH"}}`). Inside `app.py`, you'll notice a helper function called `clean_dynamo_item()` that translates this back into normal JSON so our Next.js website doesn't have to deal with it!
