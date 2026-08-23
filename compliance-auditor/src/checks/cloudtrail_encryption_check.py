import boto3
from common.findings import write_compliance_finding

_cloudtrail = boto3.client("cloudtrail")
CHECK_ID = "CIS-2.4"

def handler(event, context):
    findings = []
    trails = _cloudtrail.describe_trails().get('trailList', [])
    
    for trail in trails:
        if not trail.get('KmsKeyId'):
            finding = write_compliance_finding(
                check_id=CHECK_ID,
                title=f"CloudTrail {trail['Name']} logs are not encrypted with KMS",
                description="CloudTrail logs should be encrypted at rest using KMS.",
                severity="MEDIUM",
                resource_id=trail['TrailARN'],
                resource_type="CloudTrail::Trail",
                region="global",
                remediation="Configure CloudTrail to use a KMS key for encryption."
            )
            findings.append(finding["findingId"])

    if not findings:
        return {"check": CHECK_ID, "compliant": True}
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
