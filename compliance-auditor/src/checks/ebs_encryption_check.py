import boto3
from common.findings import write_compliance_finding

_ec2 = boto3.client("ec2")
CHECK_ID = "CIS-4.1"

def handler(event, context):
    findings = []
    region = _ec2.meta.region_name
    
    paginator = _ec2.get_paginator('describe_volumes')
    for page in paginator.paginate():
        for vol in page['Volumes']:
            vol_id = vol['VolumeId']
            if not vol.get('Encrypted', False):
                finding = write_compliance_finding(
                    check_id=CHECK_ID,
                    title=f"EBS volume {vol_id} is not encrypted",
                    description="EBS volume is not encrypted at rest.",
                    severity="MEDIUM",
                    resource_id=vol_id,
                    resource_type="EC2::Volume",
                    region=region,
                    remediation="Encrypt the EBS volume or recreate it with encryption enabled."
                )
                findings.append(finding["findingId"])
                
    if not findings:
        return {"check": CHECK_ID, "compliant": True}
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
