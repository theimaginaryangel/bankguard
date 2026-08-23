# Shared Findings Schema

Table: `Findings` (DynamoDB)

**Partition key:** `findingType` — `"COMPLIANCE"` | `"FRAUD"`
**Sort key:** `findingId` — ULID (sortable by creation order, globally unique)

**GSI: `severity-index`**
- PK: `severity` — `"CRITICAL"` | `"HIGH"` | `"MEDIUM"` | `"LOW"`
- SK: `findingId`
- Purpose: query all findings above a severity threshold across both finding types in one call — this is what powers the frontend's "critical findings" header stat.

## Common envelope (every item)

| Field | Type | Notes |
|---|---|---|
| `findingId` | String | ULID |
| `findingType` | String | `COMPLIANCE` \| `FRAUD` |
| `severity` | String | `CRITICAL` \| `HIGH` \| `MEDIUM` \| `LOW` |
| `title` | String | Human-readable, e.g. "S3 bucket publicly readable" |
| `description` | String | |
| `createdAt` | String | ISO 8601 |
| `status` | String | `OPEN` \| `ACKNOWLEDGED` \| `RESOLVED` |
| `remediation` | String | What to do about it |

## `complianceDetails` (present when `findingType == COMPLIANCE`)

| Field | Type | Notes |
|---|---|---|
| `resourceId` | String | e.g. ARN |
| `resourceType` | String | e.g. `S3::Bucket` |
| `checkId` | String | e.g. `CIS-2.1` |
| `region` | String | |

## `fraudDetails` (present when `findingType == FRAUD`)

| Field | Type | Notes |
|---|---|---|
| `transactionId` | String | |
| `riskScore` | Number | 0–1, isolation forest output |
| `triggeredRules` | List\<String\> | Which rule-layer checks fired, if any |
| `contributingFeatures` | Map | Feature name → deviation, for explainability |
| `amount` | Number | |
| `merchantCategory` | String | |

## Access patterns this schema is designed for

1. Get recent findings, all types — query by `findingType`, sorted by `findingId` (ULID sorts chronologically).
2. Get findings by severity across both types — query `severity-index`.
3. Get a single finding's detail — get item by `findingType` + `findingId`.
4. Filter compliance findings by check — application-side filter on `complianceDetails.checkId` after querying `findingType = COMPLIANCE` (add a GSI on `checkId` later only if this becomes a real bottleneck).

Design this *before* writing check/detection logic — retrofitting the schema after both pipelines exist means touching both.
