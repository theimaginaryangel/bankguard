# Fraud Monitor

Welcome to the Fraud Monitor! 🕵️‍♂️

This folder contains the code for a system that catches suspicious credit card transactions. 

## How It Works

Imagine a bucket (an AWS S3 Bucket) sitting in the cloud. Every day, a bank drops a file (a CSV) full of yesterday's transactions into this bucket.

When the file drops, it wakes up our "worker" (an AWS Lambda Function). The worker reads the file line by line and runs every transaction through two tests:

1. **The Rule Engine (`src/rules/engine.py`)**: These are simple, fast rules. For example: "Did they spend over $1,000?" or "Did they buy from a sketchy jewelry store?"
2. **The AI Model (`src/model/inference.py`)**: This is our "Isolation Forest". It's a machine learning algorithm that has looked at millions of transactions and learned what "normal" looks like. If a transaction looks weird (an anomaly), it flags it with a Risk Score.

If a transaction fails either test, the worker grabs a notepad (our DynamoDB `Findings` table) and writes it down. If it fails *both* tests, it grabs a megaphone (an SNS Topic) and shouts "CRITICAL ALERT!" so an investigator can look at it immediately.

## Why Isolation Forest?

Machine learning can be complicated, but Isolation Forest is beautifully simple. 

Imagine a forest of trees. Most trees look exactly the same and are clumped closely together. But one tree has bright purple leaves and stands all by itself. It's very easy to draw a fence around that single tree to **isolate** it. 

The algorithm does exactly this with data. If a transaction is very easy to isolate from the rest of the data, it's considered an anomaly (fraud!).

## How to Test It Locally

Because the real-world dataset from Kaggle doesn't have merchant names or account IDs (it's anonymized for privacy), we need to add fake ones so our Rule Engine works.

1. Download the [Kaggle Credit Card Fraud dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).
2. Save it inside the `src/model/` folder as `creditcard.csv`.
3. Open your terminal, go to `src/model/`, and run `python prep_data.py`. This creates a new file called `creditcard_augmented.csv` with fake merchants and account IDs.
4. Run `python train.py`. This will teach the AI what normal looks like, and save its "brain" into `model.joblib`. 

When you deploy this using AWS SAM, the AWS Lambda function will load that brain and use it on new files!
