# BankGuard Web Dashboard

A responsive, dark-mode web interface built with **Next.js** and **Tailwind CSS** providing unified security posture and transactional fraud telemetry for operators and auditors.

---

## 🖥️ Pages & Features

- **`/` (System Overview):** Real-time severity summary counters for Critical and High findings across Compliance and Fraud pipelines, accompanied by architecture walkthrough links.
- **`/compliance` (Compliance Findings):** Automated audit view against the 12 CIS AWS Foundations Benchmark controls, showing failing control IDs, severity badges, affected resource identifiers, and actionable remediation steps.
- **`/fraud` (Fraud Monitor):** 
  - **S3 Direct Batch Upload:** In-browser XHR upload zone supporting CSV files up to 1GB with real-time percentage progress bars.
  - **Demo Dataset Downloader:** One-click download of a pre-formatted Kaggle-style CSV containing synthetic PCA feature variations and known anomalies.
  - **Live Processing Monitor:** Polls backend Lambda byte stream progress and model retraining status via `/processing-status/{id}`.
  - **Explainable Findings Table:** Displays flagged transaction IDs, risk score progress bars, triggered heuristic rules, and top contributing PCA deviations.
- **`/architecture` (System Architecture):** Detailed architectural blueprints explaining how DynamoDB single-table design, serverless workers, and REST endpoints converge.

---

## ⚙️ Environment Configuration

Create a `.env.local` file inside `frontend/` (or rely on production defaults in `src/lib/api.ts`):

```env
NEXT_PUBLIC_API_URL=https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod
```

---

## 🛠️ Local Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

