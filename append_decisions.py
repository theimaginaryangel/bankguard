import os

new_decisions = """
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
"""

with open("docs/decisions.md", "a", encoding="utf-8") as f:
    f.write(new_decisions)
