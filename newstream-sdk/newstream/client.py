import requests
import json
import time
import uuid

class NewStream:
    """
    NewStream SDK — stream every AI session event in real time.
    """

    def __init__(self, base_url: str, api_key: str, session_id: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session_id = session_id or str(uuid.uuid4())
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }

    def track(self, event_type: str, data: dict):
        payload = {
            "type": event_type,
            "session_id": self.session_id,
            "timestamp": int(time.time() * 1000),
            **data
        }
        r = requests.post(
            f"{self.base_url}/sessions/{self.session_id}/events",
            json=payload,
            headers=self.headers,
            timeout=5
        )
        r.raise_for_status()
        return r.json()

    def token(self, text: str, model: str = None, latency_ms: int = None):
        return self.track("token", {"text": text, "model": model, "latency_ms": latency_ms})

    def tool_call(self, tool: str, input: dict, output: dict = None, latency_ms: int = None):
        return self.track("tool_call", {"tool": tool, "input": input, "output": output, "latency_ms": latency_ms})

    def error(self, message: str, error_type: str = None):
        return self.track("error", {"message": message, "error_type": error_type})

    def metadata(self, **kwargs):
        return self.track("metadata", kwargs)

    def done(self, total_tokens: int = None, total_latency_ms: int = None):
        return self.track("done", {"total_tokens": total_tokens, "total_latency_ms": total_latency_ms})
