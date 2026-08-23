# Decisions Log

Written as decisions are made, not reconstructed afterward. Each entry: what was decided, why, and what the alternative would have cost.

---

## 2026-08 — SAM before Terraform

**Decision:** Build and deploy both pipelines in AWS SAM first. Migrate to Terraform only after the SAM version is working and validated.

**Why:** SAM is purpose-built for serverless — it abstracts a lot of the Lambda/API Gateway/event-source wiring that Terraform makes you write out by hand, and `sam local invoke` gives a fast local test loop. At this stage the open question is "does the check logic work," not "which IaC tool" — SAM lets that question get answered fastest.

**Alternative considered:** Terraform from the start. Rejected because it means learning AWS service behavior and Terraform's state/HCL model at the same time, which is a slower way to learn either one. Building in SAM first, then re-implementing the same infrastructure in Terraform, isolates the variables — the second pass is purely a Terraform lesson because the "what" is already solved.

---

## 2026-08 — Shared findings schema across both pipelines

**Decision:** One DynamoDB table (`Findings`), partitioned by `findingType` (`COMPLIANCE` | `FRAUD`), with type-specific detail fields nested under `complianceDetails` / `fraudDetails`.

**Why:** The frontend and API layer should not need to know which backend produced a finding. A single table with a shared envelope (severity, title, description, status, remediation) plus a discriminated detail block lets both pipelines evolve independently while the read side stays simple.

**Alternative considered:** Two separate tables. Rejected — it would push the "unify compliance and fraud findings" problem onto the API/frontend layer instead of solving it once at the data model.

---

## 2026-08 — Fraud detection: rules + isolation forest, not rules-only or deep learning

**Decision:** Hybrid — a fast rule layer (amount deviation, velocity, merchant category flags) plus an isolation forest trained on the Kaggle credit card fraud dataset for anomaly scoring.

**Why:** Rules alone is the common baseline and doesn't demonstrate applied ML. A full deep-learning approach would be disproportionate to a dataset this size and harder to explain/defend. Isolation forest gives genuine anomaly detection while staying explainable — each flagged transaction can be attached to the specific features that drove its score, rather than a black-box output.

---

## 2026-08 — Batch processing, not simulated real-time streaming

**Decision:** The fraud monitor processes transactions in batches from S3, not as a simulated live stream.

**Why:** The Kaggle dataset is static. Simulating real-time ingestion on top of static historical data would be presentation theater — it doesn't reflect anything true about the system. A batch pipeline with a documented path to streaming (e.g., swapping the S3 trigger for a Kinesis consumer) is the honest framing and holds up under a direct question about it.

---

## 2026-08 — Curated 12-check compliance list, not the full CIS benchmark

**Decision:** 12 checks spanning IAM, S3, CloudTrail, security groups, and EBS — not the full CIS AWS Foundations Benchmark (which runs to 50+ controls).

**Why:** Scope control. 12 checks, each one understood well enough to explain unprompted, is more defensible than 50 checks copied from a compliance tool without the underlying reasoning behind each one.

---

## 2026-08 — API Layer: "Lambda Lith" Pattern

**Decision:** Use a single AWS Lambda function to handle all API routing (`/findings`, `/stats/summary`) rather than creating a separate Lambda for each endpoint.

**Why:** For a small, read-only API, creating 3-4 separate Lambdas introduces unnecessary complexity in the SAM template and slower cold starts across the board. A single Python script using simple `if/elif` path routing keeps the codebase beginner-friendly, highly readable, and dramatically simplifies the CloudFormation/SAM configuration.

---

## 2026-08 — Frontend: Next.js + Tailwind CSS, No State Managers

**Decision:** Build the frontend using Next.js and Tailwind CSS, relying entirely on React's built-in `useState` and `useEffect` for data fetching instead of heavy libraries like Redux or React Query.

**Why:** The goal of the frontend is to be a transparent "window" into the backend engineering. Adding heavy frontend state-management would obscure the simple fetch-and-display nature of the dashboard. Tailwind CSS was chosen so that all styling remains co-located with the HTML, allowing anyone reading the code to immediately understand how the layout is constructed without tracing through separate CSS files.

---

## 2026-08 — Infrastructure as Code: Skipping Terraform

**Decision:** Retain AWS SAM as the sole IaC tool, skipping the planned Phase 5 Terraform migration.

**Why:** The portfolio already contains robust demonstrations of Terraform in other projects. Migrating this specific project to Terraform would add redundant proof of skill while unnecessarily duplicating the infrastructure configuration. SAM remains the perfect, idiomatic choice for a heavily Serverless architecture.
