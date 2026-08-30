import boto3
import json
import csv
import os
import time
import urllib.parse
from common.findings import write_fraud_finding
from rules.engine import run_rules
from model.inference import score_transaction, retrain_model

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
dynamodb = boto3.client('dynamodb')

# Configurable threshold via environment variable (default: 0.4)
AI_RISK_THRESHOLD = float(os.environ.get("AI_RISK_THRESHOLD", "0.4"))
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
TABLE_NAME = os.environ.get("FINDINGS_TABLE_NAME", "Findings")

def update_job_progress(job_id, processed_bytes, total_bytes, status=None):
    try:
        if status is None:
            status = 'COMPLETED' if processed_bytes >= total_bytes else 'PROCESSING'
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item={
                'findingType': {'S': 'JOB_PROGRESS'},
                'findingId': {'S': job_id},
                'processedBytes': {'N': str(processed_bytes)},
                'totalBytes': {'N': str(total_bytes)},
                'status': {'S': status},
                'timestamp': {'S': str(int(time.time()))}
            }
        )
    except Exception as e:
        print(f"Failed to update progress: {e}")

def clear_old_fraud_findings():
    try:
        exclusive_start_key = None
        deleted_count = 0
        while True:
            query_kwargs = {
                'TableName': TABLE_NAME,
                'KeyConditionExpression': "findingType = :ft",
                'ExpressionAttributeValues': {":ft": {"S": "FRAUD"}}
            }
            if exclusive_start_key:
                query_kwargs['ExclusiveStartKey'] = exclusive_start_key
                
            response = dynamodb.query(**query_kwargs)
            items = response.get('Items', [])
            for item in items:
                dynamodb.delete_item(
                    TableName=TABLE_NAME,
                    Key={'findingType': {'S': 'FRAUD'}, 'findingId': item['findingId']}
                )
                deleted_count += 1
                
            exclusive_start_key = response.get('LastEvaluatedKey')
            if not exclusive_start_key:
                break
        print(f"Cleared {deleted_count} old fraud findings.")
    except Exception as e:
        print(f"Error clearing findings: {e}")

def lambda_handler(event, context):
    # Wipe old fraud findings on every new batch upload to keep the dashboard clean
    clear_old_fraud_findings()
    
    for record in event.get('Records', []):
        bucket_name = record['s3']['bucket']['name']
        file_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        job_id = file_key.split('/')[-1] # The filename is the job ID
        
        print(f"Reading new file {file_key} from bucket {bucket_name}...")
        
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            total_bytes = response.get('ContentLength', 0)
            processed_bytes = 0
            update_job_progress(job_id, 0, total_bytes, status='PROCESSING')
            
            # Read all rows to memory for dynamic ML learning and processing
            byte_stream = response['Body']
            lines = []
            for line_bytes in byte_stream.iter_lines():
                if line_bytes:
                    processed_bytes += len(line_bytes) + 1
                    try:
                        lines.append(line_bytes.decode('utf-8', errors='replace'))
                    except Exception:
                        pass

            if not lines:
                print("Empty file uploaded.")
                update_job_progress(job_id, total_bytes, total_bytes, status='COMPLETED')
                continue

            csv_reader = csv.DictReader(lines)
            rows = list(csv_reader)
            
            if not rows:
                update_job_progress(job_id, total_bytes, total_bytes, status='COMPLETED')
                continue

            # --- DYNAMIC ML LEARNING STEP ---
            # If the uploaded file contains ML features (V1..V28), retrain the IsolationForest model dynamically
            first_row = rows[0]
            has_pca = any(f"V{i}" in first_row for i in range(1, 29))
            if has_pca:
                print(f"Detected PCA features in dataset with {len(rows)} rows. Triggering dynamic ML retraining...")
                retrain_model(rows)

            # --- SCORING & FINDINGS GENERATION ---
            row_count = 0
            flagged_count = 0
            
            for transaction in rows:
                row_count += 1
                try:
                    # Normalize user custom dataset columns to expected schema
                    if 'transaction_dollar_amount' in transaction and 'Amount' not in transaction:
                        transaction['Amount'] = transaction['transaction_dollar_amount']
                    elif 'amount' in transaction and 'Amount' not in transaction:
                        transaction['Amount'] = transaction['amount']
                        
                    if 'credit_card' in transaction and 'accountId' not in transaction:
                        transaction['accountId'] = transaction['credit_card']
                    elif 'account_id' in transaction and 'accountId' not in transaction:
                        transaction['accountId'] = transaction['account_id']
                        
                    if 'merchant_category' in transaction and 'merchantCategory' not in transaction:
                        transaction['merchantCategory'] = transaction['merchant_category']
                    elif 'merchant' in transaction and 'merchantCategory' not in transaction:
                        transaction['merchantCategory'] = transaction['merchant']

                    # 1. Run fast heuristic rules
                    triggered_rules = run_rules(transaction)
                    
                    # 2. Run smart AI model
                    risk_score, contributing_features = score_transaction(transaction)
                    
                    is_fraud = False
                    severity = "LOW"
                    
                    if len(triggered_rules) > 0 or risk_score >= AI_RISK_THRESHOLD:
                        is_fraud = True
                        if len(triggered_rules) > 0 and risk_score >= AI_RISK_THRESHOLD:
                            severity = "CRITICAL"
                        elif risk_score >= AI_RISK_THRESHOLD:
                            severity = "HIGH"
                        else:
                            severity = "MEDIUM"
                    
                    if is_fraud:
                        flagged_count += 1
                        tx_id = transaction.get('accountId') or transaction.get('credit_card') or f"tx_{row_count}"
                        raw_amount = transaction.get('Amount') or transaction.get('amount') or 0.0
                        merchant = transaction.get('merchantCategory') or transaction.get('merchant') or 'unknown'
                        
                        try:
                            parsed_amount = float(raw_amount or 0.0)
                        except (ValueError, TypeError):
                            parsed_amount = 0.0

                        write_fraud_finding(
                            title=f"Suspicious Transaction: {tx_id}",
                            description="Transaction flagged by Fraud Monitor rules/AI.",
                            severity=severity,
                            transaction_id=tx_id,
                            risk_score=risk_score,
                            triggered_rules=triggered_rules,
                            contributing_features=contributing_features,
                            amount=parsed_amount,
                            merchant_category=merchant
                        )
                        
                        if severity == "CRITICAL" and SNS_TOPIC_ARN:
                            try:
                                message = f"CRITICAL FRAUD ALERT! Transaction {tx_id} flagged by rules & AI. Risk Score: {risk_score:.2f}, Amount: ${parsed_amount:.2f}"
                                sns_client.publish(
                                    TopicArn=SNS_TOPIC_ARN,
                                    Message=message,
                                    Subject="Critical Fraud Finding"
                                )
                            except Exception as sns_err:
                                print(f"Failed to publish to SNS: {sns_err}")
                except Exception as row_err:
                    print(f"Error processing row {row_count}: {row_err}")
                    continue

            print(f"Batch processing finished. Scanned {row_count} rows, flagged {flagged_count} potential frauds.")
            update_job_progress(job_id, total_bytes, total_bytes, status='COMPLETED')

        except Exception as file_err:
            print(f"Fatal error processing file {file_key}: {file_err}")
            update_job_progress(job_id, 0, 0, status='FAILED')

    return {
        'statusCode': 200,
        'body': json.dumps('Batch processing complete!')
    }
