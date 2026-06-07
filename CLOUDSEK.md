# NewStream — CloudSek Integration Guide

**Backend:** https://api.maskllm.com/
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
curl -X POST https://api.maskllm.com/sessions/{session_id}/events \
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

NEWSTREAM_URL = "https://api.maskllm.com"
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
const NEWSTREAM_URL = "https://api.maskllm.com/";
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
## Example 

```app.py
import time
import requests
from google import genai

# -----------------------------------
# CONFIG
# -----------------------------------

GEMINI_API_KEY = "AQ.Ab8RN6L6EsqjSOdPYfF7-P5xEObFKvoG0S6YBhXYPc78OQri3w"

NEWSTREAM_URL = "https://api.maskllm.com"
NEWSTREAM_KEY = "cloudsek-ceb2f11ae252633ef7e45634dd055672"

# -----------------------------------
# GEMINI CLIENT
# -----------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)

session_id = f"gemini-{int(time.time())}"

# -----------------------------------
# TRACK FUNCTION
# -----------------------------------

def track(event_type: str, data: dict):
    try:
        requests.post(
            f"{NEWSTREAM_URL}/sessions/{session_id}/events",
            headers={
                "Content-Type": "application/json",
                "x-api-key": NEWSTREAM_KEY
            },
            json={
                "type": event_type,
                "timestamp": int(time.time() * 1000),
                **data
            },
            timeout=5
        )
    except Exception as e:
        print("Tracking failed:", e)

# -----------------------------------
# SEND METADATA
# -----------------------------------

track("metadata", {
    "provider": "google",
    "model": "gemini-2.5-flash"
})

# -----------------------------------
# REAL LLM CALL
# -----------------------------------

try:
    start = time.time()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain how AI works in a few words",
    )

    text = response.text

    print("\nAssistant:\n")
    print(text)

    # SEND RESPONSE EVENT
    track("token", {
        "text": text,
        "model": "gemini-2.5-flash",
        "latency_ms": int((time.time() - start) * 1000)
    })

    # DONE EVENT
    track("done", {
        "total_tokens": len(text.split()),
        "total_latency_ms": int((time.time() - start) * 1000)
    })

except Exception as e:

    track("error", {
        "message": str(e),
        "error_type": type(e).__name__
    })

    raise
```

run -- 
```bash
curl https://api.maskllm.com/sessions
```
```bash
$ curl https://api.maskllm.com/sessions/gemini-1780834595/replay
```

example response, 
```bash
$ curl https://api.maskllm.com/sessions/gemini-1780834595/replay
{"session_id":"gemini-1780834595","events":[{"type":"metadata","timestamp":1780834595147,"provider":"google","model":"gemini-2.5-flash"},{"type":"token","timestamp":1780834602389,"text":"It learns patterns from data to make decisions.","model":"gemini-2.5-flash","latency_ms":5575},{"type":"done","timestamp":1780834603336,"total_tokens":8,"total_latency_ms":6522}],"count":3}
```
---


## View Your Sessions

### List all sessions
```bash
curl https://api.maskllm.com/sessions
```

### Replay a full session
```bash
curl https://api.maskllm.com/sessions/{session_id}/replay
```

Returns every event in order from start to finish.

### Watch a session live (real time)
```bash
curl https://api.maskllm.com/sessions/{session_id}/live
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
curl -X POST https://api.maskllm.com/sessions/cloudsek-test/events \
  -H "Content-Type: application/json" \
  -H "x-api-key: cloudsek-ceb2f11ae252633ef7e45634dd055672" \
  -d '{"type": "token", "text": "test event", "model": "gpt-4"}'

curl https://api.maskllm.com/sessions/cloudsek-test/replay
```

Second curl should return your event.

---

## Support

Any issues — reach out directly.
