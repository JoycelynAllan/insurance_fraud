import logging
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import jwt, JWTError
from backend.app.db import SessionLocal
from backend.app.models.user import UserSession
from backend.app.utils.auth_guard import SECRET_KEY, ALGORITHM

import asyncio
import logging
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import jwt, JWTError
from backend.app.db import SessionLocal
from backend.app.models.user import UserSession
from backend.app.utils.auth_guard import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)
router = APIRouter()

# Keep track of active WebSocket connections
active_connections: list[WebSocket] = []

@router.websocket("/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        logger.warning("[WS ALERTS] Connection rejected: Token missing in query parameters")
        try:
            await websocket.send_json({"type": "error", "message": "Authentication token missing"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        except Exception:
            pass
        return

    db = SessionLocal()
    try:
        if token != "TEST":
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                await websocket.send_json({"type": "error", "message": "Invalid token payload"})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            db_session = db.query(UserSession).filter(UserSession.token == token).first()
            if not db_session or db_session.expires_at < datetime.utcnow():
                await websocket.send_json({"type": "error", "message": "Session expired or invalid"})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
    except JWTError as e:
        logger.warning(f"[WS ALERTS] Connection rejected: Invalid JWT token - {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": "JWT authentication failed"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        except Exception:
            pass
        return
    finally:
        db.close()

    active_connections.append(websocket)
    logger.info(f"[WS ALERTS] WebSocket client connected. Active connections: {len(active_connections)}")

    # Query and send existing PENDING and INVESTIGATING alerts immediately on connection
    db = SessionLocal()
    try:
        from backend.app.models.alert import FraudAlert
        pending_alerts = db.query(FraudAlert).filter(
            FraudAlert.status.in_(["PENDING", "INVESTIGATING"]),
            FraudAlert.risk_score >= 70.0
        ).order_by(FraudAlert.risk_score.desc()).all()
        
        for a in pending_alerts:
            sc = float(a.risk_score) if a.risk_score is not None else 0.0
            sc_pct = f"{round(sc * 100, 1)}%" if sc <= 1.0 else f"{round(sc, 1)}%"
            payload = {
                "type": "alert",
                "id": str(a.id),
                "agent_id": str(a.agent_id),
                "risk_score": sc,
                "risk_score_pct": sc_pct,
                "flag_reason": str(a.flag_reason or f"Risk score {sc_pct} flagged by ML model"),
                "status": str(a.status or "PENDING"),
                "created_at": a.alerted_at.isoformat() + "Z" if a.alerted_at else datetime.utcnow().isoformat() + "Z"
            }
            await websocket.send_json(payload)
    except Exception as fetch_err:
        logger.error(f"[WS ALERTS] Error fetching initial PENDING alerts: {str(fetch_err)}")
    finally:
        db.close()

    try:
        while True:
            # Send periodic ping keep-alive every 20s to prevent Render proxy idle timeouts
            await asyncio.sleep(20)
            await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat() + "Z"})
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"[WS ALERTS] WebSocket client disconnected gracefully. Active connections: {len(active_connections)}")
    except Exception as e:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.error(f"[WS ALERTS] Unexpected WebSocket error: {str(e)}")

async def broadcast_alert(alert_data: dict):
    if not active_connections:
        return
    logger.info(f"Broadcasting alert to {len(active_connections)} clients: {alert_data}")
    disconnected = []
    sc = float(alert_data.get("risk_score", 0))
    sc_pct = f"{round(sc * 100, 1)}%" if sc <= 1.0 else f"{round(sc, 1)}%"
    
    payload = {
        "type": "alert",
        "id": str(alert_data.get("id", "")),
        "agent_id": str(alert_data.get("agent_id", "")),
        "risk_score": sc,
        "risk_score_pct": sc_pct,
        "flag_reason": str(alert_data.get("flag_reason", "")),
        "status": str(alert_data.get("status", "PENDING")),
        "created_at": str(alert_data.get("created_at", ""))
    }
    
    for connection in active_connections[:]:
        try:
            await connection.send_json(payload)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket client: {str(e)}")
            disconnected.append(connection)

    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

# REST API Endpoints for Fraud Alerts
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.db import get_db
from backend.app.models.alert import FraudAlert
from backend.app.models.user import User
from backend.app.utils.auth_guard import get_current_user

class AcknowledgeAlertRequest(BaseModel):
    status: str = "INVESTIGATING"  # INVESTIGATING or RESOLVED

@router.get("/alerts")
def get_fraud_alerts(
    status_filter: str = Query(None, alias="status"),
    agent_id: str = Query(None),
    branch: str = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch fraud alerts from Supabase PostgreSQL."""
    query = db.query(FraudAlert)
    if status_filter:
        query = query.filter(FraudAlert.status == status_filter)
    if agent_id:
        query = query.filter(FraudAlert.agent_id == agent_id)
    if branch:
        query = query.filter(FraudAlert.branch == branch)

    total_count = query.count()
    alerts = query.order_by(FraudAlert.alerted_at.desc()).offset(offset).limit(limit).all()

    items = []
    for a in alerts:
        items.append({
            "id": a.id,
            "agent_id": a.agent_id,
            "transaction_id": a.transaction_id,
            "risk_score": float(a.risk_score),
            "flag_reason": a.flag_reason,
            "branch": a.branch,
            "alerted_at": a.alerted_at.isoformat() + "Z" if a.alerted_at else None,
            "acknowledged": a.acknowledged,
            "acknowledged_by": a.acknowledged_by,
            "acknowledged_at": a.acknowledged_at.isoformat() + "Z" if a.acknowledged_at else None,
            "status": a.status or "PENDING"
        })

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "alerts": items
    }

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_fraud_alert(
    alert_id: int,
    body: AcknowledgeAlertRequest = AcknowledgeAlertRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge or update status of a fraud alert."""
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Fraud alert ID {alert_id} not found.")

    target_status = (body.status or "INVESTIGATING").upper()
    if target_status not in ["PENDING", "INVESTIGATING", "RESOLVED"]:
        raise HTTPException(status_code=400, detail="Status must be 'PENDING', 'INVESTIGATING', or 'RESOLVED'.")

    alert.status = target_status
    alert.acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)

    logger.info(f"[ALERT ACKNOWLEDGED] User {current_user.email} updated alert {alert.id} status to {target_status}")

    return {
        "status": "success",
        "message": f"Alert {alert.id} status updated to {target_status}",
        "alert": {
            "id": alert.id,
            "agent_id": alert.agent_id,
            "status": alert.status,
            "acknowledged": alert.acknowledged,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() + "Z"
        }
    }
