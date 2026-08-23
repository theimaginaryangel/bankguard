import boto3
from common.findings import write_compliance_finding

_s3 = boto3.client("s3")
CHECK_ID = "CIS-2.1"

def handler(event, context):
    findings = []
    buckets = _s3.list_buckets().get('Buckets', [])
    
    for b in buckets:
        bucket_name = b['Name']
        try:
            pab = _s3.get_public_access_block(Bucket=bucket_name)
            conf = pab.get('PublicAccessBlockConfiguration', {})
            if not (conf.get('BlockPublicAcls') and conf.get('IgnorePublicAcls') and 
                    conf.get('BlockPublicPolicy') and conf.get('RestrictPublicBuckets')):
                finding = write_compliance_finding(
                    check_id=CHECK_ID,
                    title=f"S3 bucket {bucket_name} does not block all public access",
                    description="Bucket is missing one or more Block Public Access settings.",
                    severity="CRITICAL",
                    resource_id=f"arn:aws:s3:::{bucket_name}",
                    resource_type="S3::Bucket",
                    region="global", # S3 is global namespace, though buckets are regional
                    remediation="Enable all Block Public Access settings for this bucket."
                )
                findings.append(finding["findingId"])
        except _s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                finding = write_compliance_finding(
                    check_id=CHECK_ID,
                    title=f"S3 bucket {bucket_name} has no public access block",
                    description="Bucket does not have any Block Public Access settings configured.",
                    severity="CRITICAL",
                    resource_id=f"arn:aws:s3:::{bucket_name}",
                    resource_type="S3::Bucket",
                    region="global",
                    remediation="Enable Block Public Access for this bucket."
                )
                findings.append(finding["findingId"])

    if not findings:
        return {"check": CHECK_ID, "compliant": True}
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
