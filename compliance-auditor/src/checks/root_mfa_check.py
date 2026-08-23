"""
CIS-1.2 — Root account has MFA enabled.

Why this check exists: the root account has unrestricted access to every
resource in the account and can't be fully restricted by IAM policy. If it's
compromised without MFA in place, there is no secondary control standing
between an attacker and full account takeover. This is why it's ranked
CRITICAL and checked first, ahead of anything else in the benchmark.

What it does: calls iam.get_account_summary(), which returns
AccountMFAEnabled as 1 or 0 for the root account. No root credentials or
root sign-in are required to run this check — it reads account-level
summary data via a standard IAM permission.
"""
import boto3
from common.findings import write_compliance_finding

_iam = boto3.client("iam")

CHECK_ID = "CIS-1.2"


def handler(event, context):
    summary = _iam.get_account_summary()
    mfa_enabled = summary["SummaryMap"].get("AccountMFAEnabled", 0) == 1

    if mfa_enabled:
        # Compliant — no finding written. See docs/decisions.md for why
        # passing checks don't get a row in the table.
        return {"check": CHECK_ID, "compliant": True}

    finding = write_compliance_finding(
        check_id=CHECK_ID,
        title="Root account does not have MFA enabled",
        description=(
            "The AWS account root user does not have multi-factor "
            "authentication enabled. The root user has unrestricted "
            "access and cannot be fully constrained by IAM policy, "
            "making MFA the primary control against full account "
            "compromise if root credentials are exposed."
        ),
        severity="CRITICAL",
        resource_id="root-account",
        resource_type="IAM::RootAccount",
        region="global",
        remediation=(
            "Sign in as the root user and enable a virtual or hardware "
            "MFA device under IAM > Security credentials > Multi-factor "
            "authentication (MFA)."
        ),
    )
    return {"check": CHECK_ID, "compliant": False, "findingId": finding["findingId"]}
