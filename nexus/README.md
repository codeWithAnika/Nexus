# NEXUS — AI-Powered Criminal Intelligence & Network Analysis Platform

**Connecting the dots. Revealing hidden networks.**

A frontend prototype built for Smart India Hackathon. NEXUS turns fragmented
investigation data (calls, transfers, movements, associations) into an
explainable network view: an interactive graph, entity risk profiles, hidden
connection discovery, alerts, and a case report — all backed by a single
consistent fictional dataset, **Operation Nexus**.

This is a decision-support tool. Risk indicators are explained as patterns
that warrant further review, never as findings of guilt.

## Tech stack

React 19 · Vite · Tailwind CSS · React Router · Framer Motion · Recharts ·
Cytoscape.js (`react-cytoscapejs`) · Lucide icons · Axios (mock service layer)

## Getting started

```bash
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`). Log in with
any Investigator ID and password — authentication is mocked for this
prototype.

```bash
npm run build     # production build to /dist
npm run preview   # preview the production build
```

## Project structure

```
src/
├── components/
│   ├── layout/          Shell, Sidebar, Topbar
│   ├── dashboard/        Stats, risk chart, recent cases, alerts feed, mini network
│   ├── investigation/    Network graph, entity panel, filters, discovery + upload modals, timeline
│   └── common/           Shared primitives (risk badge)
├── pages/
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   ├── Cases.jsx
│   ├── Investigation.jsx   ← the core workspace
│   ├── Alerts.jsx
│   └── Reports.jsx
├── data/mockData.js      Single consistent fictional dataset + BFS pathfinding
├── services/api.js       Async service layer, shaped for a real backend later
└── utils/entityVisuals.js
```

## The story: Operation Nexus

18 entities across people, phone numbers, financial accounts, an offshore
account, two organizations, a warehouse, a vehicle, a shared burner device,
and an observed meeting — forming two communities (a financial cluster around
Meridian Trade Solutions, and a logistics cluster around Falcon Freight) that
are bridged by a single high-risk entity, Arjun Mehta. Five alerts, a seven-
step timeline, and the network graph all reference the same underlying data.

## Connecting a real backend

`src/services/api.js` already mirrors the intended REST surface
(`GET /cases`, `GET /cases/:id/network`, `GET /entities/:id`, `GET /alerts`,
`POST /evidence/upload`, `GET /reports/:caseId`). Swap each function body for
an `axios` call against your API and no page or component needs to change.

## Notes on this prototype

- Authentication, evidence processing, and file parsing are simulated.
- Hidden Connection Discovery runs a real breadth-first search over the mock
  relationship graph — try Arjun Mehta ↔ any entity in the opposite cluster.
- The report's Export button uses the browser print dialog; wire up a real
  PDF export when a backend is available.
