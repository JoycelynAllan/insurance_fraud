# Phase 3 Sprint Logs

## Week 6 — Real-Time Alert Backend & Frontend Setup
- Installed frontend dependencies: `recharts`, `axios`, `socket.io-client`.
- Created WebSocket endpoint `/api/alerts` in `backend/app/routes/alerts.py` to maintain active client sockets and broadcast fraud alerts.
- Configured modular routes inside `backend/app/routes/agents.py` containing `/api/agents/risk` and `/api/agents/{agent_id}/trend`.
- Refactored `backend/app/routes/analyze.py` to maintain only the `POST /api/analyze` route.
- Customised the `DashboardNavbar` component to support showing the custom title and real-time GMT+0 Ghana time, which updates every second.

## Week 7 — Composed Dashboard & Background Services
- Created composed views at `material-dashboard-react/src/views/Dashboard/FraudDashboard.js` integrating the four key dashboard components:
  - **AgentRiskTable**: Renders list of scored agents with branch/status, support text searches, custom row selections, and color-coded risk alerts.
  - **AlertPanel**: Opens a WebSocket connection to the backend alert stream, prepending new items instantly and handling close/reconnect errors.
  - **BranchHeatmap**: Formats and groups overall risk averages per branch and plots them in a custom Recharts `BarChart` using Material colors.
  - **PaymentTrendChart**: Renders transaction trend line plot with a dynamic reference line marking the agent's mean transaction amount.
- Wired navigation inside `src/routes.js` to add the `/fraud` path with the warning icon.
- Configured default and wildcard routing redirects in `src/App.js` to land on `/fraud` by default.
- Implemented background `AsyncIOScheduler` worker in `backend/app/services/scheduler.py` running every 5 minutes to score the 10 most recent transactions and broadcast warnings for scores >= 70.
- Registered background scheduler worker startup and shutdown lifecycle hooks inside the FastAPI `lifespan` context in `backend/app/main.py`.

## Problems Hit & Solutions

### ESLint & Prettier Rules
- **Problem**: React production compilation failed due to missing prop validations on subcomponents (like Recharts Tooltip) and prettier formatting rule warnings.
- **Solution**: Explicitly defined `CustomTooltip.propTypes` for Custom Tooltips inside `PaymentTrendChart.js` and `BranchHeatmap.js`. Formatted all modified and new files with `npx prettier --write` before building the app.

### FastAPI Dependencies
- **Problem**: FastAPI failed to launch on model loading due to `ModuleNotFoundError: No module named 'apscheduler'`.
- **Solution**: Ran `pip install -r backend/requirements.txt` to align the virtual environment packages, which successfully installed all 16 required dependencies.
