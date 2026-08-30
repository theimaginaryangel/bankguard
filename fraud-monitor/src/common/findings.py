import boto3
import os
import uuid
import time
from datetime import datetime, timezone

# We get our table name from our environment variables (set in template.yaml)
TABLE_NAME = os.environ.get("FINDINGS_TABLE_NAME", "Findings")

# We only want to set up our connection to DynamoDB once
_dynamodb = boto3.client("dynamodb")

def write_fraud_finding(title, description, severity, transaction_id, risk_score, triggered_rules, contributing_features, amount, merchant_category):
    """
    This function takes all the details about a suspicious transaction 
    and saves them as a "finding" into our DynamoDB database.
    """
    # Timestamp-prefixed findingId ensures chronological sorting when queried with ScanIndexForward=False
    ts_ms = int(time.time() * 1000)
    finding_id = f"{ts_ms}-{uuid.uuid4().hex[:8]}"
    
    # We grab the current time so we know exactly when we found this
    created_at = datetime.now(timezone.utc).isoformat()
    
    safe_tx_id = str(transaction_id or "unknown_tx")
    safe_amount = str(amount if amount is not None and str(amount).strip() != "" else 0.0)
    safe_risk_score = str(risk_score if risk_score is not None and str(risk_score).strip() != "" else 0.0)
    safe_merchant = str(merchant_category or "unknown")

    # Here we are preparing the 'Item' exactly how DynamoDB likes it.
    item = {
        # --- Shared Envelope Fields ---
        "findingType": {"S": "FRAUD"},          # This tells the frontend it's a Fraud finding
        "findingId": {"S": finding_id},
        "severity": {"S": severity or "MEDIUM"},# "CRITICAL", "HIGH", "MEDIUM", or "LOW"
        "title": {"S": title or f"Suspicious Transaction: {safe_tx_id}"},
        "description": {"S": description or "Transaction flagged by Fraud Monitor rules/AI."},
        "createdAt": {"S": created_at},
        "status": {"S": "OPEN"},                # All new findings start as "OPEN"
        "remediation": {"S": "Review transaction and contact customer to confirm activity."},
        
        # --- Fraud Specific Fields ---
        "fraudDetails": {"M": {                 # 'M' stands for Map (a dictionary)
            "transactionId": {"S": safe_tx_id},
            "riskScore": {"N": safe_risk_score}, # Isolation Forest score
            "amount": {"N": safe_amount},
            "merchantCategory": {"S": safe_merchant},
            "triggeredRules": {"L": [{"S": str(rule)} for rule in (triggered_rules or [])]}, # 'L' stands for List
            "contributingFeatures": {"M": {
                # Convert our features into a DynamoDB map format.
                str(k): {"N": str(v)} for k, v in (contributing_features or {}).items()
            }}
        }}
    }
    
    # Send the prepared item to DynamoDB!
    _dynamodb.put_item(TableName=TABLE_NAME, Item=item)
    
    # We return the finding back so the caller knows the finding ID
    return item
