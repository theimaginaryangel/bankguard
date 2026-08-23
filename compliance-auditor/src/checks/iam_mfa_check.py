import boto3
from common.findings import write_compliance_finding

_iam = boto3.client("iam")
CHECK_ID = "CIS-1.3"

def handler(event, context):
    paginator = _iam.get_paginator('list_users')
    findings = []
    
    for page in paginator.paginate():
        for user in page['Users']:
            user_name = user['UserName']
            # Check if user has console access (LoginProfile)
            has_console = False
            try:
                _iam.get_login_profile(UserName=user_name)
                has_console = True
            except _iam.exceptions.NoSuchEntityException:
                pass
            
            if has_console:
                # Check MFA
                mfa_devices = _iam.list_mfa_devices(UserName=user_name)
                if not mfa_devices['MFADevices']:
                    finding = write_compliance_finding(
                        check_id=CHECK_ID,
                        title=f"IAM user {user_name} has console access but no MFA",
                        description=f"User {user_name} can log into the console without MFA.",
                        severity="HIGH",
                        resource_id=user['Arn'],
                        resource_type="IAM::User",
                        region="global",
                        remediation="Enable MFA for the user."
                    )
                    findings.append(finding["findingId"])
                    
    if not findings:
        return {"check": CHECK_ID, "compliant": True}
        
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
