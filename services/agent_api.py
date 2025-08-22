# services/agent_api.py
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("UI_API_KEY")  # optional X-API-Key header
TIMEOUT = int(os.getenv("UI_HTTP_TIMEOUT", "60"))

def agent_url() -> str:
    return AGENT_API_URL

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    if API_KEY:
        s.headers["X-API-Key"] = API_KEY
    return s

def ping_backend() -> bool:
    try:
        r = _session().get(f"{AGENT_API_URL}/health", timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def call_plan_api(profile: dict) -> dict:
    r = _session().post(f"{AGENT_API_URL}/v1/plan", data=json.dumps(profile), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()
