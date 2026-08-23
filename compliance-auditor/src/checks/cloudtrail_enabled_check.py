import boto3
from common.findings import write_compliance_finding

_cloudtrail = boto3.client("cloudtrail")
CHECK_ID = "CIS-2.3"

def handler(event, context):
    trails = _cloudtrail.describe_trails().get('trailList', [])
    
    has_multi_region = False
    for trail in trails:
        if trail.get('IsMultiRegionTrail'):
            # Check if it's logging
            status = _cloudtrail.get_trail_status(Name=trail['TrailARN'])
            if status.get('IsLogging'):
                has_multi_region = True
                break

    if has_multi_region:
        return {"check": CHECK_ID, "compliant": True}

    finding = write_compliance_finding(
        check_id=CHECK_ID,
        title="CloudTrail is not enabled across all regions",
        description="No multi-region CloudTrail is currently configured and logging.",
        severity="HIGH",
        resource_id="aws-account",
        resource_type="CloudTrail::Trail",
        region="global",
        remediation="Create a multi-region CloudTrail and enable logging."
    )
    
    return {"check": CHECK_ID, "compliant": False, "findingId": finding["findingId"]}
