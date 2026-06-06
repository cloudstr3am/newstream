# NewStream — CloudSek Integration Guide

**Backend:** https://newstream-production.up.railway.app  
**API Key:** `cloudsek-ceb2f11ae252633ef7e45634dd055672`

---

## What This Does

Every time one of your customers runs an AI session, NewStream captures it — every token, tool call, error, and completion — stores it durably, and lets you watch it live or replay it any time.

You send us HTTP POST requests. We handle everything else.

---

## No Setup Required

No library to install. No dependencies. Just HTTP.

---

## Send an Event

```bash
curl -X POST https://newstream-production.up.railway.app/sessions/{session_id}/events \
  -H "Content-Type: application/json" \
  -H "x-api-key: cloudsek-ceb2f11ae252633ef7e45634dd055672" \
  -d '{"type": "token", "text": "Hello", "model": "gpt-4", "latency_ms": 45}'
```

Replace `{session_id}` with your own identifier — typically your customer's user ID or session ID.

---

## Instrument Your AI App

Pick whichever language your AI backend is in.

### Python

```python
import requests
import time

NEWSTREAM_URL = "https://newstream-production.up.railway.app"
NEWSTREAM_KEY = "cloudsek-ceb2f11ae252633ef7e45634dd055672"

def track(session_id: str, event_type: str, data: dict):
    requests.post(
        f"{NEWSTREAM_URL}/sessions/{session_id}/events",
        headers={
            "Content-Type": "application/json",
            "x-api-key": NEWSTREAM_KEY
        },
        json={
            "type": event_type,
            "session_id": session_id,
            "timestamp": int(time.time() * 1000),
            **data
        },
        timeout=5
    )
```

Use it anywhere in your AI pipeline:

```python
session_id = "customer-123-session-456"

track(session_id, "metadata", {"customer_id": "123", "plan": "enterprise"})
track(session_id, "token", {"text": "Hello", "model": "gpt-4", "latency_ms": 450})
track(session_id, "tool_call", {"tool": "threat_search", "input": {"query": "ransomware"}, "output": {"results": 5}})
track(session_id, "error", {"message": "Rate limit hit", "error_type": "RateLimitError"})
track(session_id, "done", {"total_tokens": 350, "total_latency_ms": 4200})
```

### Node.js

```javascript
const NEWSTREAM_URL = "https://newstream-production.up.railway.app";
const NEWSTREAM_KEY = "cloudsek-ceb2f11ae252633ef7e45634dd055672";

async function track(sessionId, eventType, data) {
    await fetch(`${NEWSTREAM_URL}/sessions/${sessionId}/events`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": NEWSTREAM_KEY
        },
        body: JSON.stringify({
            type: eventType,
            session_id: sessionId,
            timestamp: Date.now(),
            ...data
        })
    });
}

// Usage
await track("customer-123", "token", { text: "Hello", model: "gpt-4", latency_ms: 45 });
await track("customer-123", "done", { total_tokens: 150 });
```

---

## Or Use Our SDK (Optional)

If you prefer a cleaner interface, install our SDK:

```bash
pip install newstream
```

```python
from newstream import NewStream

stream = NewStream(
    base_url="https://newstream-production.up.railway.app",
    api_key="cloudsek-ceb2f11ae252633ef7e45634dd055672",
    session_id="customer-123-session-456"
)

stream.token("Hello", model="gpt-4", latency_ms=45)
stream.tool_call("threat_search", {"query": "ransomware"}, {"results": 5})
stream.error("Rate limit hit", error_type="RateLimitError")
stream.done(total_tokens=350, total_latency_ms=4200)
```

---

## View Your Sessions

### List all sessions
```bash
curl https://newstream-production.up.railway.app/sessions
```

### Replay a full session
```bash
curl https://newstream-production.up.railway.app/sessions/{session_id}/replay
```

Returns every event in order from start to finish.

### Watch a session live (real time)
```bash
curl https://newstream-production.up.railway.app/sessions/{session_id}/live
```

Streams events as they happen via SSE. Keep this open while a customer session runs and you see every event appear in real time.

---

## Event Types

| Type | When to send | Fields |
|------|-------------|--------|
| `token` | Every AI output token or response | `text`, `model`, `latency_ms` |
| `tool_call` | Every tool or function call | `tool`, `input`, `output`, `latency_ms` |
| `error` | Any exception or failure | `message`, `error_type` |
| `metadata` | Customer/session context | any key-value pairs |
| `done` | Session complete | `total_tokens`, `total_latency_ms` |

---

## Test It Right Now

```bash
curl -X POST https://newstream-production.up.railway.app/sessions/cloudsek-test/events \
  -H "Content-Type: application/json" \
  -H "x-api-key: cloudsek-ceb2f11ae252633ef7e45634dd055672" \
  -d '{"type": "token", "text": "test event", "model": "gpt-4"}'

curl https://newstream-production.up.railway.app/sessions/cloudsek-test/replay
```

Second curl should return your event.

---

## Support

Any issues — reach out directly.
