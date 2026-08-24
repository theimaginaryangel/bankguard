import boto3
import json
import csv
import os
import io
import codecs
import time
import urllib.parse
from common.findings import write_fraud_finding
from rules.engine import run_rules
from model.inference import score_transaction

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
dynamodb = boto3.client('dynamodb')

# How weird does it have to be for the AI to flag it? (0.0 to 1.0)
AI_RISK_THRESHOLD = 0.7 
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
TABLE_NAME = os.environ.get("FINDINGS_TABLE_NAME", "Findings")

def update_job_progress(job_id, processed_bytes, total_bytes):
    try:
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item={
                'findingType': {'S': 'JOB_PROGRESS'},
                'findingId': {'S': job_id},
                'processedBytes': {'N': str(processed_bytes)},
                'totalBytes': {'N': str(total_bytes)},
                'status': {'S': 'PROCESSING' if processed_bytes < total_bytes else 'COMPLETED'},
                'timestamp': {'S': str(int(time.time()))}
            }
        )
    except Exception as e:
        print(f"Failed to update progress: {e}")

def lambda_handler(event, context):
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        job_id = file_key.split('/')[-1] # The filename is the job ID
        
        print(f"Reading new file {file_key} from bucket {bucket_name}...")
        
        # We start the progress at 0%
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        total_bytes = response['ContentLength']
        processed_bytes = 0
        update_job_progress(job_id, 0, total_bytes)
        
        # Use streaming so we don't run out of memory on 1GB Kaggle files!
        byte_stream = response['Body']
        text_stream = codecs.iterdecode(byte_stream, 'utf-8')
        
        # We wrap it in a generator to count bytes processed
        def byte_counting_stream():
            nonlocal processed_bytes
            for line in text_stream:
                processed_bytes += len(line.encode('utf-8'))
                yield line

        csv_reader = csv.DictReader(byte_counting_stream())
        
        row_count = 0
        for transaction in csv_reader:
            row_count += 1
            
            # Normalize user's custom dataset columns to our expected schema
            if 'transaction_dollar_amount' in transaction:
                transaction['Amount'] = transaction['transaction_dollar_amount']
            if 'credit_card' in transaction:
                transaction['accountId'] = transaction['credit_card']
                
            # Run our fast, simple rules
            triggered_rules = run_rules(transaction)
            
            # Run our slower, smart AI model
            risk_score, contributing_features = score_transaction(transaction)
            
            is_fraud = False
            severity = "LOW"
            
            if len(triggered_rules) > 0 or risk_score > AI_RISK_THRESHOLD:
                is_fraud = True
                
                if len(triggered_rules) > 0 and risk_score > AI_RISK_THRESHOLD:
                    severity = "CRITICAL"
                elif risk_score > AI_RISK_THRESHOLD:
                    severity = "HIGH"
                else:
                    severity = "MEDIUM"
            
            if is_fraud:
                tx_id = transaction.get('accountId', 'unknown_tx') 
                amount = transaction.get('Amount', 0)
                merchant = transaction.get('merchantCategory', 'unknown')
                
                write_fraud_finding(
                    title=f"Suspicious Transaction: {tx_id}",
                    description="Transaction flagged by Fraud Monitor rules/AI.",
                    severity=severity,
                    transaction_id=tx_id,
                    risk_score=risk_score,
                    triggered_rules=triggered_rules,
                    contributing_features=contributing_features,
                    amount=amount,
                    merchant_category=merchant
                )
                
                if severity == "CRITICAL" and SNS_TOPIC_ARN:
                    message = f"CRITICAL FRAUD ALERT! Transaction {tx_id} flagged by both rules and AI. Score: {risk_score:.2f}"
                    sns_client.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Message=message,
                        Subject="Critical Fraud Finding"
                    )
            
            # Update progress every 500 rows to avoid spamming DynamoDB too much
            if row_count % 500 == 0:
                update_job_progress(job_id, processed_bytes, total_bytes)

        # Mark as 100% completed
        update_job_progress(job_id, total_bytes, total_bytes)

    return {
        'statusCode': 200,
        'body': json.dumps('Batch processing complete!')
    }
