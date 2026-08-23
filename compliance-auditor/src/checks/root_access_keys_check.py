import boto3
from common.findings import write_compliance_finding

_iam = boto3.client("iam")
CHECK_ID = "CIS-1.1"

def handler(event, context):
    summary = _iam.get_account_summary()
    keys_present = summary["SummaryMap"].get("AccountAccessKeysPresent", 0)

    if keys_present == 0:
        return {"check": CHECK_ID, "compliant": True}

    finding = write_compliance_finding(
        check_id=CHECK_ID,
        title="Root account has active access keys",
        description="The AWS account root user has active access keys.",
        severity="CRITICAL",
        resource_id="root-account",
        resource_type="IAM::RootAccount",
        region="global",
        remediation="Delete root access keys and use IAM roles instead."
    )
    return {"check": CHECK_ID, "compliant": False, "findingId": finding["findingId"]}
