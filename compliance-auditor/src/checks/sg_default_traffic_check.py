import boto3
from common.findings import write_compliance_finding

_ec2 = boto3.client("ec2")
CHECK_ID = "CIS-3.2"

def handler(event, context):
    findings = []
    region = _ec2.meta.region_name
    
    paginator = _ec2.get_paginator('describe_security_groups')
    for page in paginator.paginate(Filters=[{'Name': 'group-name', 'Values': ['default']}]):
        for sg in page['SecurityGroups']:
            sg_id = sg['GroupId']
            vpc_id = sg.get('VpcId', 'classic')
            
            # Default SG should restrict all traffic (no inbound, no outbound rules)
            has_rules = len(sg.get('IpPermissions', [])) > 0 or len(sg.get('IpPermissionsEgress', [])) > 0
            
            if has_rules:
                finding = write_compliance_finding(
                    check_id=CHECK_ID,
                    title=f"Default security group for VPC {vpc_id} allows traffic",
                    description="The default security group should not have any inbound or outbound rules.",
                    severity="MEDIUM",
                    resource_id=sg_id,
                    resource_type="EC2::SecurityGroup",
                    region=region,
                    remediation="Remove all rules from the default security group."
                )
                findings.append(finding["findingId"])
                
    if not findings:
        return {"check": CHECK_ID, "compliant": True}
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
