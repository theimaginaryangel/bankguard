import boto3
import json
import csv
import os
import io
from common.findings import write_fraud_finding
from rules.engine import run_rules
from model.inference import score_transaction

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# How weird does it have to be for the AI to flag it? (0.0 to 1.0)
AI_RISK_THRESHOLD = 0.7 
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

def lambda_handler(event, context):
    """
    This is the "front door" of our Fraud Monitor. 
    When S3 says "Hey! A new batch of transactions arrived!", this function wakes up.
    """
    
    # 1. Figure out which file triggered us
    # Sometimes an event has multiple files (records), so we loop through them.
    for record in event.get('Records', []):
        bucket_name = record['s3']['bucket']['name']
        file_key = record['s3']['object']['key']
        
        print(f"Reading new file {file_key} from bucket {bucket_name}...")
        
        # 2. Download the file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read().decode('utf-8')
        
        # 3. Parse the CSV data
        # We use io.StringIO to pretend our string is a file so the CSV reader can read it.
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        # 4. Check every single transaction!
        for transaction in csv_reader:
            
            # Run our fast, simple rules
            triggered_rules = run_rules(transaction)
            
            # Run our slower, smart AI model
            risk_score, contributing_features = score_transaction(transaction)
            
            # 5. Decide if it's fraudulent
            is_fraud = False
            severity = "LOW"
            
            # If it broke ANY rules, or the AI thinks it's weird, we flag it.
            if len(triggered_rules) > 0 or risk_score > AI_RISK_THRESHOLD:
                is_fraud = True
                
                # Determine Severity
                if len(triggered_rules) > 0 and risk_score > AI_RISK_THRESHOLD:
                    severity = "CRITICAL" # Both the rules AND the AI flagged it!
                elif risk_score > AI_RISK_THRESHOLD:
                    severity = "HIGH"     # Just the AI
                else:
                    severity = "MEDIUM"   # Just the rules
            
            # 6. Save the finding to the database
            if is_fraud:
                # We try to grab the accountId, but default to 'unknown' if it's missing
                tx_id = transaction.get('accountId', 'unknown_tx') 
                amount = transaction.get('Amount', 0)
                merchant = transaction.get('merchantCategory', 'unknown')
                
                finding = write_fraud_finding(
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
                
                # 7. Shout into the megaphone if it's a CRITICAL alert
                if severity == "CRITICAL" and SNS_TOPIC_ARN:
                    message = f"CRITICAL FRAUD ALERT! Transaction {tx_id} flagged by both rules and AI. Score: {risk_score:.2f}"
                    sns_client.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Message=message,
                        Subject="Critical Fraud Finding"
                    )

    return {
        'statusCode': 200,
        'body': json.dumps('Batch processing complete!')
    }
