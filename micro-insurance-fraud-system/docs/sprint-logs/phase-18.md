## Phase 18 — Fix WebSocket Alerts Connection Flapping & Proxy Keep-Alive (Week 22)

### Root Cause Analysis
1. **Unaccepted Connection Close:**
   - In `backend/app/routes/alerts.py`, calling `websocket.close()` prior to `websocket.accept()` on unauthenticated requests threw internal Starlette exceptions and generated immediate client drop frames.

2. **Render Proxy Idle Connection Timeout:**
   - Render's HTTP/1.1 proxy automatically terminates idle WebSocket connections if no data frames pass for ~50 seconds.
   - `await websocket.receive_text()` in `alerts.py` waited for client text frames. Because `AlertPanel.js` does not send client text frames, the connection remained idle until Render's proxy closed it, triggering immediate frontend disconnects and instant reconnect attempts.

---

### What Was Built
- **Accept-First Session Validation ([`alerts.py`](file:///c:/Users/Apoka/Downloads/investment_project/micro-insurance-fraud-system/backend/app/routes/alerts.py)):**
  - Updated `websocket_endpoint` to call `await websocket.accept()` first.
  - If token validation or session state fails, sends a JSON error frame (`{"type": "error", ...}`) prior to closing gracefully.

- **20-Second Ping Keep-Alive Loop:**
  - Replaced blocking `receive_text()` loop with an `asyncio.sleep(20)` keep-alive loop sending `{"type": "ping", "timestamp": ...}` every 20 seconds, keeping Render's proxy and browser sockets connected indefinitely.

- **Frontend Ping Filtering & Exponential Backoff ([`AlertPanel.js`](file:///c:/Users/Apoka/Downloads/investment_project/material-dashboard-react/src/components/AlertPanel.js)):**
  - Filtered server ping messages (`if (data && (data.type === "ping" || data.type === "error")) return;`).
  - Added exponential backoff reconnect logic starting at 3s and capping at 30s (`delay = Math.min(delay * 1.5, 30000)`).

---

### Verification
- `npm run build` executed and passed cleanly in `material-dashboard-react`.
- Python syntax compiled successfully for `backend/app/routes/alerts.py`.
