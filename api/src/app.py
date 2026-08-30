import boto3
import json
import os
import urllib.parse
from collections import defaultdict

# We get our database table name from the environment variables
TABLE_NAME = os.environ.get("FINDINGS_TABLE_NAME", "Findings")
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET_NAME")

# We set up our connection to DynamoDB and S3
_dynamodb = boto3.client("dynamodb")
_s3 = boto3.client("s3")


def lambda_handler(event, context):
    """
    This is the "front door" for our API. Whenever the Next.js website asks for data,
    AWS sends the request to this function.
    """
    path = event.get('path', '')
    
    # CORS headers allowing cross-origin requests from the Next.js dashboard
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Content-Type": "application/json"
    }
    
    try:
        # Handle CORS Preflight requests immediately
        if event.get("httpMethod") == "OPTIONS":
            return build_response(200, {}, headers)
            
        # Route requests
        if path == "/findings":
            query_params = event.get('queryStringParameters') or {}
            finding_type = query_params.get('type') # e.g. "FRAUD" or "COMPLIANCE"
            data = get_findings(finding_type)
            return build_response(200, data, headers)
            
        elif path.startswith("/findings/"):
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2:
                finding_id = parts[1]
                finding_type = (event.get('queryStringParameters') or {}).get('type', 'COMPLIANCE')
                data = get_single_finding(finding_type, finding_id)
                if data:
                    return build_response(200, data, headers)
                else:
                    return build_response(404, {"error": "Finding not found"}, headers)
                    
        elif path == "/overview-data":
            data = get_stats_summary()
            return build_response(200, data, headers)
            
        elif path.startswith("/processing-status/"):
            parts = [p for p in path.split("/") if p]
            job_id = parts[1] if len(parts) >= 2 else None
            if not job_id:
                return build_response(400, {"error": "Missing job ID"}, headers)
            
            job_id = urllib.parse.unquote(job_id)
            
            try:
                response = _dynamodb.get_item(
                    TableName=TABLE_NAME,
                    Key={
                        'findingType': {'S': 'JOB_PROGRESS'},
                        'findingId': {'S': job_id}
                    }
                )
                item = response.get('Item')
                if item:
                    return build_response(200, clean_dynamo_item(item), headers)
                else:
                    return build_response(404, {"error": "Job not started yet"}, headers)
            except Exception as e:
                print(f"DynamoDB Error: {e}")
                return build_response(500, {"error": "Database error"}, headers)

        elif path == "/upload-url" and event.get("httpMethod") == "POST":
            raw_body = event.get("body")
            body = {}
            if raw_body:
                try:
                    body = json.loads(raw_body)
                except Exception:
                    body = {}
                    
            raw_filename = body.get("filename", "upload.csv")
            # Sanitize filename to prevent S3 key path traversal
            safe_filename = os.path.basename(raw_filename)
            if not safe_filename or safe_filename == ".":
                safe_filename = "upload.csv"
            if not safe_filename.lower().endswith(".csv"):
                safe_filename += ".csv"
            
            presigned_post = _s3.generate_presigned_post(
                Bucket=UPLOAD_BUCKET,
                Key=f"uploads/{safe_filename}",
                Fields={},
                Conditions=[
                    ["content-length-range", 1, 1073741824] # 1 byte to 1GB max
                ],
                ExpiresIn=3600 # Ticket expires in 1 hour
            )
            return build_response(200, presigned_post, headers)
            
        return build_response(404, {"error": f"Path {path} not found"}, headers)
        
    except Exception as e:
        print(f"Unhandled Error: {e}")
        return build_response(500, {"error": "Internal Server Error"}, headers)


# --- Helper Functions ---

def get_findings(finding_type=None):
    """
    Fetches the latest findings from the database.
    """
    if not finding_type:
        finding_type = "COMPLIANCE"
        
    response = _dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="findingType = :type",
        ExpressionAttributeValues={
            ":type": {"S": finding_type}
        },
        ScanIndexForward=False, # Newest first
        Limit=50
    )
    
    clean_items = [clean_dynamo_item(item) for item in response.get('Items', [])]
    return clean_items


def get_single_finding(finding_type, finding_id):
    """
    Fetches one exact finding using its Partition Key (findingType) and Sort Key (findingId).
    """
    response = _dynamodb.get_item(
        TableName=TABLE_NAME,
        Key={
            "findingType": {"S": finding_type},
            "findingId": {"S": finding_id}
        }
    )
    
    item = response.get('Item')
    if item:
        return clean_dynamo_item(item)
    return None


def get_stats_summary():
    """
    Counts up findings by severity and findingType across the entire table using pagination.
    """
    stats = {
        "COMPLIANCE": defaultdict(int),
        "FRAUD": defaultdict(int)
    }
    
    exclusive_start_key = None
    while True:
        scan_kwargs = {
            'TableName': TABLE_NAME,
            'ProjectionExpression': "findingType, severity, #s",
            'ExpressionAttributeNames': {"#s": "status"}
        }
        if exclusive_start_key:
            scan_kwargs['ExclusiveStartKey'] = exclusive_start_key
            
        response = _dynamodb.scan(**scan_kwargs)
        for item in response.get('Items', []):
            f_type = item.get('findingType', {}).get('S', 'UNKNOWN')
            severity = item.get('severity', {}).get('S', 'UNKNOWN')
            status = item.get('status', {}).get('S', 'OPEN')
            
            if status == "OPEN" and f_type in stats:
                stats[f_type][severity] += 1
                
        exclusive_start_key = response.get('LastEvaluatedKey')
        if not exclusive_start_key:
            break
            
    return stats


def clean_dynamo_value(val_dict):
    """
    Recursively unpacks a DynamoDB typed attribute value.
    """
    if not isinstance(val_dict, dict) or not val_dict:
        return val_dict
        
    data_type = list(val_dict.keys())[0]
    data_val = val_dict[data_type]
    
    if data_type == "S":
        return data_val
    elif data_type == "N":
        try:
            return float(data_val) if '.' in data_val else int(data_val)
        except ValueError:
            return data_val
    elif data_type == "M":
        return {k: clean_dynamo_value(v) for k, v in data_val.items()}
    elif data_type == "L":
        return [clean_dynamo_value(item) for item in data_val]
    elif data_type == "BOOL":
        return data_val
    elif data_type == "NULL":
        return None
    else:
        return data_val


def clean_dynamo_item(item):
    """
    Translates DynamoDB's typed dictionary into standard Python dictionary.
    """
    return {k: clean_dynamo_value(v) for k, v in item.items()}


def build_response(status_code, body, headers):
    """
    Formats the response for AWS API Gateway.
    """
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body)
    }


