# BankGuard Frontend

Welcome to the Next.js Frontend! 🖥️

This is the web dashboard that recruiters or auditors will look at. It acts as a window into our database, showing us all the hard work our Compliance Auditor and Fraud Monitor have been doing in the background.

## How it works

This is a **Next.js** application built with **Tailwind CSS**. To keep the code beginner-friendly and easy to read:
- All the styling is done right inside the HTML (using Tailwind classes like `bg-blue-500`).
- We don't use complex state management (like Redux). We just use simple React `useEffect` hooks to fetch data when the page loads.
- The data is fetched from our API Layer. The API URLs are managed in `src/lib/api.ts`.

## How to run it locally

1. Open your terminal and go to this `frontend` folder.
2. Install the required packages by running:
   ```bash
   npm install
   ```
3. Start the development server by running:
   ```bash
   npm run dev
   ```
4. Open your web browser and go to [http://localhost:3000](http://localhost:3000).

*(Note: If the API isn't deployed yet, the dashboard will still load, but the tables will be empty!)*

## Pages Included
- **`/` (Overview):** Shows big summary numbers and an explanation of the dashboard.
- **`/compliance`:** A table of all the CIS security configuration alerts.
- **`/fraud`:** A table of the suspicious credit card transactions caught by our rules and AI.
- **`/architecture`:** A plain-English explanation of how the whole system works together in the cloud.
