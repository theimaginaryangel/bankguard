import boto3
from common.findings import write_compliance_finding

_s3 = boto3.client("s3")
CHECK_ID = "CIS-2.2"

def handler(event, context):
    findings = []
    buckets = _s3.list_buckets().get('Buckets', [])
    
    for b in buckets:
        bucket_name = b['Name']
        try:
            _s3.get_bucket_encryption(Bucket=bucket_name)
            # Default encryption is enabled
        except _s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                finding = write_compliance_finding(
                    check_id=CHECK_ID,
                    title=f"S3 bucket {bucket_name} does not have default encryption enabled",
                    description="Bucket is missing default server-side encryption.",
                    severity="MEDIUM",
                    resource_id=f"arn:aws:s3:::{bucket_name}",
                    resource_type="S3::Bucket",
                    region="global",
                    remediation="Enable default encryption for the S3 bucket."
                )
                findings.append(finding["findingId"])

    if not findings:
        return {"check": CHECK_ID, "compliant": True}
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
