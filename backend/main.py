import os
import httpx
import base64
import json
import time
import asyncio
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from typing import Optional

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

TOKEN = os.getenv("S2_ACCESS_TOKEN")
BASIN = os.getenv("S2_BASIN")
API_KEY = os.getenv("API_KEY")
BASIN_URL = f"https://{BASIN}.b.s2.dev/v1"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")

app = FastAPI(title="NewStream")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def check_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

async def push_to_loki(session_id: str, event: dict):
    ts = str(time.time_ns())
    payload = {
        "streams": [{
            "stream": {"session_id": session_id, "type": event.get("type", "unknown"), "app": "newstream"},
            "values": [[ts, json.dumps(event)]]
        }]
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{LOKI_URL}/loki/api/v1/push", json=payload)
    except Exception:
        pass

@app.get("/health")
async def health():
    return {"status": "ok", "basin": BASIN}

@app.post("/sessions/{session_id}/events")
async def append_event(session_id: str, request: Request, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    body = await request.json()
    data = base64.b64encode(json.dumps(body).encode()).decode()
    async with httpx.AsyncClient() as client:
        await client.put(f"{BASIN_URL}/streams/{session_id}", headers=HEADERS, json={})
        r = await client.post(
            f"{BASIN_URL}/streams/{session_id}/records",
            headers={**HEADERS, "s2-format": "base64"},
            json={"records": [{"body": data}]}
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
    await push_to_loki(session_id, body)
    return {"ok": True}

@app.get("/sessions")
async def list_sessions():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASIN_URL}/streams", headers=HEADERS)
        r.raise_for_status()
        return {"sessions": [s["name"] for s in r.json().get("streams", [])]}

@app.get("/sessions/{session_id}/replay")
async def replay(session_id: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        tail_r = await client.get(f"{BASIN_URL}/streams/{session_id}/records/tail", headers=HEADERS)
        tail_r.raise_for_status()
        tail_seq = tail_r.json()["tail"]["seq_num"]
        if tail_seq == 0:
            return {"session_id": session_id, "events": [], "count": 0}
        r = await client.get(
            f"{BASIN_URL}/streams/{session_id}/records",
            headers={**HEADERS, "s2-format": "base64"},
            params={"seq_num": 0, "count": tail_seq}
        )
        r.raise_for_status()
        events = [json.loads(base64.b64decode(rec["body"])) for rec in r.json().get("records", [])]
        return {"session_id": session_id, "events": events, "count": len(events)}

@app.get("/sessions/{session_id}/live")
async def live(session_id: str):
    async def event_stream():
        async with httpx.AsyncClient(timeout=30.0) as client:
            tail_r = await client.get(
                f"{BASIN_URL}/streams/{session_id}/records/tail", headers=HEADERS
            )
            tail_r.raise_for_status()
            seq = tail_r.json()["tail"]["seq_num"]

        while True:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(
                        f"{BASIN_URL}/streams/{session_id}/records",
                        headers={**HEADERS, "s2-format": "base64"},
                        params={"seq_num": seq, "count": 100}
                    )
                    if r.status_code == 200:
                        records = r.json().get("records", [])
                        for rec in records:
                            event = json.loads(base64.b64decode(rec["body"]))
                            yield f"data: {json.dumps(event)}\n\n"
                            seq += 1
                        if not records:
                            await asyncio.sleep(0.5)
                    else:
                        await asyncio.sleep(0.5)
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=True)
