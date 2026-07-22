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
    token = websocket.query_params.get("token")
    if not token:
        # Reject connection without token
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    db = SessionLocal()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        db_session = db.query(UserSession).filter(UserSession.token == token).first()
        if not db_session or db_session.expires_at < datetime.utcnow():
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    finally:
        db.close()

    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    try:
        while True:
            # Maintain connection alive, listen for text messages (we ignore them)
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")
    except Exception as e:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.error(f"WebSocket connection error: {str(e)}")

async def broadcast_alert(alert: dict):
    if not active_connections:
        return
    logger.info(f"Broadcasting alert to {len(active_connections)} clients: {alert}")
    alert_str = json.dumps(alert)
    for connection in active_connections[:]:
        try:
            await connection.send_text(alert_str)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket client: {str(e)}")
            if connection in active_connections:
                active_connections.remove(connection)
