import boto3
import datetime
from common.findings import write_compliance_finding

_iam = boto3.client("iam")
CHECK_ID = "CIS-1.4"

def handler(event, context):
    paginator = _iam.get_paginator('list_users')
    findings = []
    now = datetime.datetime.now(datetime.timezone.utc)
    
    for page in paginator.paginate():
        for user in page['Users']:
            user_name = user['UserName']
            keys = _iam.list_access_keys(UserName=user_name)['AccessKeyMetadata']
            for key in keys:
                age_days = (now - key['CreateDate']).days
                if age_days > 90:
                    finding = write_compliance_finding(
                        check_id=CHECK_ID,
                        title=f"Access key for user {user_name} is older than 90 days",
                        description=f"Access key {key['AccessKeyId']} is {age_days} days old.",
                        severity="MEDIUM",
                        resource_id=user['Arn'],
                        resource_type="IAM::AccessKey",
                        region="global",
                        remediation="Rotate access key."
                    )
                    findings.append(finding["findingId"])

    if not findings:
        return {"check": CHECK_ID, "compliant": True}
        
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
