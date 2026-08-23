# Compliance Auditor

Scheduled Lambda checks against this AWS account, evaluated against a curated set of CIS AWS Foundations Benchmark controls. Deployed with AWS SAM (see `docs/decisions.md` in the repo root for why SAM before Terraform).

## Checks implemented

| Check ID | Description | Severity | Status |
|---|---|---|---|
| CIS-1.2 | Root account has MFA enabled | CRITICAL | ✅ Implemented |
| CIS-1.1 | Root account has no active access keys | CRITICAL | ⬜ Not yet built |
| CIS-1.3 | IAM console users have MFA enabled | HIGH | ⬜ |
| CIS-1.4 | IAM access keys rotated within 90 days | MEDIUM | ⬜ |
| CIS-1.5 | No `*:*` admin policies attached directly to users | HIGH | ⬜ |
| CIS-2.1 | S3 buckets not publicly readable/writable | CRITICAL | ⬜ |
| CIS-2.2 | S3 buckets encrypted at rest | MEDIUM | ⬜ |
| CIS-2.3 | CloudTrail enabled in all regions | HIGH | ⬜ |
| CIS-2.4 | CloudTrail logs encrypted | MEDIUM | ⬜ |
| CIS-3.1 | No unrestricted ingress on 22/3389 | CRITICAL | ⬜ |
| CIS-3.2 | Default security group restricts all traffic | MEDIUM | ⬜ |
| CIS-4.1 | EBS volumes encrypted | MEDIUM | ⬜ |

Each check is a small, independent Lambda under `src/checks/`, sharing the finding-writer in `src/common/findings.py`. A check only writes a row when it fails — passing checks stay silent, so the table reflects issues, not a full audit trail (add a separate pass/fail counter later if a "coverage" stat is wanted on the frontend).

## Local setup

```bash
# from compliance-auditor/
pip install -r src/requirements.txt --target src/ --break-system-packages
sam build
```

## Test locally

```bash
sam local invoke RootMfaCheckFunction
```

This calls real AWS APIs (`iam:GetAccountSummary`) using your local AWS credentials — it doesn't touch anything in DynamoDB unless you also set `FINDINGS_TABLE_NAME` and have local access to write there. To fully dry-run without writing, comment out the `write_compliance_finding` call temporarily or point `FINDINGS_TABLE_NAME` at a throwaway local table.

## Deploy

```bash
sam deploy --guided
```

First run will prompt for a stack name, region, and confirm IAM role creation (required — the Lambda needs `iam:GetAccountSummary` and DynamoDB write access, both scoped narrowly in `template.yaml`). Subsequent deploys: `sam deploy`.

## Adding the next check

1. Add a new file under `src/checks/`, following `root_mfa_check.py`'s shape: read-only AWS API call → evaluate → `write_compliance_finding(...)` on failure.
2. Add the Lambda + its `Schedule` event to `template.yaml`, scoping its IAM policy to exactly the read permissions it needs.
3. Update the checklist above.
4. If the check surfaces something non-obvious about *why* it matters, add a line to `docs/decisions.md`.
