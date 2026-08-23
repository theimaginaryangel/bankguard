import boto3
from common.findings import write_compliance_finding

_iam = boto3.client("iam")
CHECK_ID = "CIS-1.5"

def handler(event, context):
    findings = []
    paginator = _iam.get_paginator('get_account_authorization_details')
    for page in paginator.paginate(Filter=['User']):
        for user in page['UserDetailList']:
            bad_policies = []
            
            for policy in user.get('UserPolicyList', []):
                doc = policy.get('PolicyDocument', {})
                if _is_admin_policy(doc):
                    bad_policies.append(policy.get('PolicyName'))
                    
            if bad_policies:
                finding = write_compliance_finding(
                    check_id=CHECK_ID,
                    title=f"User {user['UserName']} has direct admin policies attached",
                    description=f"User has direct admin access via policies: {', '.join(bad_policies)}",
                    severity="HIGH",
                    resource_id=user['Arn'],
                    resource_type="IAM::User",
                    region="global",
                    remediation="Use groups or roles for assigning admin policies instead of attaching them directly."
                )
                findings.append(finding["findingId"])
                
    if not findings:
        return {"check": CHECK_ID, "compliant": True}
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}

def _is_admin_policy(doc):
    statements = doc.get('Statement', [])
    if isinstance(statements, dict):
        statements = [statements]
    for s in statements:
        if s.get('Effect') == 'Allow':
            actions = s.get('Action', [])
            resources = s.get('Resource', [])
            if isinstance(actions, str): actions = [actions]
            if isinstance(resources, str): resources = [resources]
            
            if '*' in actions and '*' in resources:
                return True
    return False
