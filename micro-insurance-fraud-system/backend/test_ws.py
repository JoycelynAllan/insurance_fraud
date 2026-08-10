import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/api/alerts?token=TEST"
    try:
        async with websockets.connect(uri) as ws:
            print("Connected to live WebSocket alerts stream")
            received_alerts = 0
            for i in range(5):
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                if data.get("type") == "alert":
                    received_alerts += 1
                    print(f"ALERT RECEIVED: Agent {data.get('agent_id')} at {data.get('risk_score_pct')} (Status: {data.get('status')})")
                elif data.get("type") == "ping":
                    print("Ping received - ignored")

            if received_alerts > 0:
                print("PASSED")
            else:
                print("FAILED: No alerts received")
    except Exception as e:
        print(f"FAILED with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
