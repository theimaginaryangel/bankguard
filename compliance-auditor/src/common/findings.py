"""
Shared helper for writing findings to the DynamoDB Findings table.
Used by every compliance check Lambda — keeps the write shape consistent
with shared/findings-schema.md so the API layer never has to special-case
which check produced a finding.
"""
import os
import time
import uuid
import boto3

_dynamodb = boto3.resource("dynamodb")


def _new_finding_id() -> str:
    """
    Time-sortable ID: millisecond timestamp (hex) + random suffix.
    Not a spec-compliant ULID, but sorts chronologically like one, which is
    all the sort key needs. Swap for the `python-ulid` package if a real
    ULID becomes necessary (e.g. cross-system ID exchange).
    """
    ts_hex = format(int(time.time() * 1000), "x").zfill(12)
    rand_suffix = uuid.uuid4().hex[:8]
    return f"{ts_hex}{rand_suffix}"


def write_compliance_finding(
    *,
    check_id: str,
    title: str,
    description: str,
    severity: str,
    resource_id: str,
    resource_type: str,
    region: str,
    remediation: str,
) -> dict:
    """
    Writes one COMPLIANCE finding. Only call this when a check FAILS.
    We use a deterministic ID based on check_id and resource_id so that 
    future runs of the same check overwrite the finding instead of duplicating it!
    """
    table_name = os.environ["FINDINGS_TABLE_NAME"]
    table = _dynamodb.Table(table_name)

    finding_id = f"{check_id}-{resource_id}"

    item = {
        "findingType": "COMPLIANCE",
        "findingId": finding_id,
        "severity": severity,
        "title": title,
        "description": description,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "OPEN",
        "remediation": remediation,
        "complianceDetails": {
            "resourceId": resource_id,
            "resourceType": resource_type,
            "checkId": check_id,
            "region": region,
        },
    }
    table.put_item(Item=item)
    return item
