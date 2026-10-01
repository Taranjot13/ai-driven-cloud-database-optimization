# Frontend guide

The frontend is implemented with React and Vite and is located in the `frontend/` directory.

## Purpose

The dashboard is designed to make the database optimization workflow understandable during a university demonstration. It visualizes the monitoring layer, anomaly detection, prediction, optimization outcomes, resource health, and cost model in a concise interface.

## Pages

- Dashboard: summary metrics and decision flow
- Performance: query metrics and inspection panel
- Anomalies: anomaly counts and status breakdown
- Predictions: forecast interpretation and next-latency view
- Optimizations: history, summary cards, and explicit execution workflow
- Resources: database health and warnings
- Costs: cloud-agnostic reference pricing model
- System: status and architecture overview

## Design principles

- dark monitoring aesthetic
- card-based layout with clear status indicators
- responsive behavior for desktop and mobile layouts
- real data from the backend only
- no automatic optimization execution on page load

## Local run

```powershell
cd frontend
npm install
npm run dev
```

The default Vite port is 5173.
