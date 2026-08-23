import boto3
from common.findings import write_compliance_finding

_ec2 = boto3.client("ec2")
CHECK_ID = "CIS-3.1"

def handler(event, context):
    findings = []
    # To save costs and time, we check the current region only
    region = _ec2.meta.region_name
    
    paginator = _ec2.get_paginator('describe_security_groups')
    for page in paginator.paginate():
        for sg in page['SecurityGroups']:
            sg_id = sg['GroupId']
            bad_ports = []
            
            for perm in sg.get('IpPermissions', []):
                from_port = perm.get('FromPort')
                to_port = perm.get('ToPort')
                ip_protocol = perm.get('IpProtocol')
                
                # Check for 22 or 3389
                if ip_protocol == '-1' or (from_port is not None and to_port is not None and 
                   (from_port <= 22 <= to_port or from_port <= 3389 <= to_port)):
                    for ip_range in perm.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            bad_ports.append(f"{from_port}-{to_port}" if from_port != to_port else str(from_port))
                    for ipv6_range in perm.get('Ipv6Ranges', []):
                        if ipv6_range.get('CidrIpv6') == '::/0':
                            bad_ports.append(f"{from_port}-{to_port}" if from_port != to_port else str(from_port))
                            
            if bad_ports:
                finding = write_compliance_finding(
                    check_id=CHECK_ID,
                    title=f"Security group {sg_id} allows unrestricted ingress on high-risk ports",
                    description=f"Security group allows 0.0.0.0/0 or ::/0 ingress on: {', '.join(set(bad_ports))}.",
                    severity="CRITICAL",
                    resource_id=sg_id,
                    resource_type="EC2::SecurityGroup",
                    region=region,
                    remediation="Remove unrestricted ingress rules for ports 22 and 3389."
                )
                findings.append(finding["findingId"])
                
    if not findings:
        return {"check": CHECK_ID, "compliant": True}
    return {"check": CHECK_ID, "compliant": False, "findingIds": findings}
