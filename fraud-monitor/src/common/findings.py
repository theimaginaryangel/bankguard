import boto3
import os
import uuid
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
    
    # We use a unique ID for each finding so they don't overwrite each other.
    # In a real system we'd use a ULID (which sorts by time), but a UUID works fine here!
    finding_id = str(uuid.uuid4())
    
    # We grab the current time so we know exactly when we found this
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Here we are preparing the 'Item' exactly how DynamoDB likes it.
    # DynamoDB expects us to tell it the data type of each value (like 'S' for String, 'N' for Number)
    item = {
        # --- Shared Envelope Fields ---
        "findingType": {"S": "FRAUD"},          # This tells the frontend it's a Fraud finding
        "findingId": {"S": finding_id},
        "severity": {"S": severity},            # "CRITICAL", "HIGH", "MEDIUM", or "LOW"
        "title": {"S": title},
        "description": {"S": description},
        "createdAt": {"S": created_at},
        "status": {"S": "OPEN"},                # All new findings start as "OPEN"
        "remediation": {"S": "Review transaction and contact customer to confirm activity."},
        
        # --- Fraud Specific Fields ---
        "fraudDetails": {"M": {                 # 'M' stands for Map (a dictionary)
            "transactionId": {"S": transaction_id},
            "riskScore": {"N": str(risk_score)}, # Isolation Forest score
            "amount": {"N": str(amount)},
            "merchantCategory": {"S": merchant_category},
            "triggeredRules": {"L": [{"S": rule} for rule in triggered_rules]}, # 'L' stands for List
            "contributingFeatures": {"M": {
                # Convert our features into a DynamoDB map format.
                key: {"N": str(value)} for key, value in contributing_features.items()
            }}
        }}
    }
    
    # Send the prepared item to DynamoDB!
    _dynamodb.put_item(TableName=TABLE_NAME, Item=item)
    
    # We return the finding back so the caller knows the finding ID
    return item
