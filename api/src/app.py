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
    
    The 'event' dictionary contains all the information about the request, 
    like which URL they asked for.
    """
    
    # 1. Figure out which URL they asked for (e.g., "/findings" or "/stats/summary")
    path = event.get('path', '')
    
    # We add CORS headers to our response so the web browser allows the website to read the data.
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
            
        # 2. Act like a traffic cop and send them to the right helper function
        if path == "/findings":
            # They want a list of findings!
            # We can also check if they asked for specific filters in the URL 
            # (like /findings?type=FRAUD)
            query_params = event.get('queryStringParameters') or {}
            finding_type = query_params.get('type') # e.g. "FRAUD" or "COMPLIANCE"
            
            data = get_findings(finding_type)
            return build_response(200, data, headers)
            
        elif path.startswith("/findings/"):
            # They want a SPECIFIC finding (e.g., /findings/12345)
            # We split the URL to grab the ID at the end
            parts = path.split("/")
            if len(parts) == 3:
                finding_id = parts[2]
                finding_type = (event.get('queryStringParameters') or {}).get('type', 'COMPLIANCE')
                data = get_single_finding(finding_type, finding_id)
                
                if data:
                    return build_response(200, data, headers)
                else:
                    return build_response(404, {"error": "Finding not found"}, headers)
                    
        elif path == "/overview-data":
            # They want the dashboard numbers (e.g., "5 Critical Frauds")
            data = get_stats_summary()
            return build_response(200, data, headers)
            
        elif path.startswith("/processing-status/"):
            # The frontend wants to know how far along the Lambda is in processing a large file!
            job_id = path.split("/")[-1]
            if not job_id:
                return build_response(400, {"error": "Missing job ID"}, headers)
            
            # S3 filenames are URL encoded
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
            # Secure S3 Upload! The frontend is asking for a ticket to upload a file.
            body = json.loads(event.get("body", "{}"))
            filename = body.get("filename", "upload.csv")
            
            # We strictly enforce that the file must be a CSV and under 5MB (5242880 bytes).
            # If a hacker tries to upload an .exe or a massive 10GB file, AWS S3 will reject it!
            presigned_post = _s3.generate_presigned_post(
                Bucket=UPLOAD_BUCKET,
                Key=f"uploads/{filename}",
                Fields={},
                Conditions=[
                    ["starts-with", "$Content-Type", ""],
                    ["content-length-range", 1, 1073741824] # 1 byte to 1GB max
                ],
                ExpiresIn=3600 # Ticket expires in 1 hour
            )
            return build_response(200, presigned_post, headers)
            
        # If they ask for a URL we don't know, we politely say "Not Found"
        return build_response(404, {"error": f"Path {path} not found"}, headers)
        
    except Exception as e:
        # If something crashes, we catch it so the website doesn't just get a blank page
        print(f"Error: {e}")
        return build_response(500, {"error": "Internal Server Error"}, headers)


# --- Helper Functions (The Teller's Tasks) ---

def get_findings(finding_type=None):
    """
    Fetches the latest findings from the database.
    """
    # If they didn't specify a type, we'll just grab COMPLIANCE by default for now
    if not finding_type:
        finding_type = "COMPLIANCE"
        
    # We ask DynamoDB for everything that matches the findingType
    response = _dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="findingType = :type",
        ExpressionAttributeValues={
            ":type": {"S": finding_type}
        },
        # ScanIndexForward=False sorts them newest first (since our ID is a time-sortable ULID or UUID)
        ScanIndexForward=False, 
        Limit=50 # Let's just return the 50 most recent to keep it fast
    )
    
    # DynamoDB returns data in a clunky format ({"S": "hello"}). 
    # We use a helper to clean it up before sending it to the website.
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
    Counts up how many CRITICAL, HIGH, etc. findings we have.
    Because DynamoDB isn't a SQL database, doing "COUNT(*)" is actually hard!
    For our simple project, we will just scan the table and count them up in Python.
    (Note: In a huge bank, we would NOT scan the whole table! We would keep a running 
    tally in a separate database row).
    """
    response = _dynamodb.scan(
        TableName=TABLE_NAME,
        # We only need these three columns to do our counting, which saves memory
        ProjectionExpression="findingType, severity, #s",
        ExpressionAttributeNames={"#s": "status"} 
    )
    
    # We use defaultdict so we don't have to write "if key exists" logic
    stats = {
        "COMPLIANCE": defaultdict(int),
        "FRAUD": defaultdict(int)
    }
    
    for item in response.get('Items', []):
        f_type = item.get('findingType', {}).get('S', 'UNKNOWN')
        severity = item.get('severity', {}).get('S', 'UNKNOWN')
        status = item.get('status', {}).get('S', 'OPEN')
        
        # Only count open issues for the dashboard
        if status == "OPEN" and f_type in stats:
            stats[f_type][severity] += 1
            
    return stats


def clean_dynamo_item(item):
    """
    Translates DynamoDB's weird dictionary format: {"severity": {"S": "HIGH"}}
    into normal Python format: {"severity": "HIGH"} so our website can read it easily.
    """
    clean = {}
    for key, value in item.items():
        # Grab the first value inside the type dictionary (e.g., "S", "N", "M")
        data_type = list(value.keys())[0]
        data_val = value[data_type]
        
        if data_type == "S":
            clean[key] = data_val
        elif data_type == "N":
            # Numbers come back as strings, so we convert them
            clean[key] = float(data_val) if '.' in data_val else int(data_val)
        elif data_type == "M":
            # If it's a Map (dictionary), we clean it recursively!
            clean[key] = clean_dynamo_item(data_val)
        elif data_type == "L":
            # If it's a List, clean each item
            clean[key] = [list(i.values())[0] for i in data_val]
        else:
            clean[key] = data_val
    return clean


def build_response(status_code, body, headers):
    """
    A helper to package our data into the exact format AWS API Gateway expects.
    """
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body)
    }
# dummy


