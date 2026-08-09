import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/api/alerts?token=TEST"
    async with websockets.connect(uri) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        parsed = json.loads(msg)
        print("Received:", parsed)
        if "agent_id" in parsed and "risk_score" in parsed and "status" in parsed:
            print("WEBSOCKET TEST PASSED")
        else:
            print(f"WEBSOCKET TEST FAILED: {msg}")

if __name__ == "__main__":
    asyncio.run(test())
