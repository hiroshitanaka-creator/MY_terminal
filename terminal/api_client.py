import json
import os
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .config import PRESETS_FILE, DATA_DIR

router = APIRouter()

# ── Endpoint URL validation ────────────────────────────────────────────────────

_ALLOWED_ENDPOINTS = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com",
}


def _validate_endpoint(provider: str, endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in ("https", "http"):
        raise HTTPException(status_code=400, detail="Invalid endpoint URL scheme")
    is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme == "http" and not is_localhost:
        raise HTTPException(status_code=400, detail="HTTP endpoints are not allowed (use HTTPS)")
    if provider in _ALLOWED_ENDPOINTS:
        allowed = _ALLOWED_ENDPOINTS[provider]
        if not endpoint.startswith(allowed):
            raise HTTPException(
                status_code=400,
                detail=f"Endpoint for provider '{provider}' must start with {allowed}",
            )


# ── Preset management ─────────────────────────────────────────────────────────

DEFAULT_PRESETS = [
    {
        "id": 0,
        "name": "Anthropic Claude",
        "provider": "anthropic",
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key": "",
        "model": "claude-opus-4-6",
        "system": "You are a helpful assistant.",
        "messages": [],
    },
    {
        "id": 1,
        "name": "OpenAI GPT",
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key": "",
        "model": "gpt-4o",
        "system": "You are a helpful assistant.",
        "messages": [],
    },
    *[
        {
            "id": i,
            "name": f"Slot {i + 1}",
            "provider": "custom",
            "endpoint": "",
            "api_key": "",
            "model": "",
            "system": "",
            "messages": [],
        }
        for i in range(2, 10)
    ],
]


def load_presets() -> list[dict]:
    if not os.path.exists(PRESETS_FILE):
        return DEFAULT_PRESETS
    with open(PRESETS_FILE) as f:
        return json.load(f)


def save_presets(presets: list[dict]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PRESETS_FILE, "w") as f:
        json.dump(presets, f, indent=2)


def _strip_api_key(preset: dict) -> dict:
    """Return preset without api_key field (keys are stored in browser only)."""
    return {k: v for k, v in preset.items() if k != "api_key"}


@router.get("/api/presets")
async def get_presets():
    return [_strip_api_key(p) for p in load_presets()]


@router.put("/api/presets/{slot_id}")
async def save_preset(slot_id: int, request: Request):
    data = await request.json()
    data.pop("api_key", None)  # never persist API keys server-side
    presets = load_presets()
    if 0 <= slot_id < len(presets):
        presets[slot_id] = {**presets[slot_id], **data, "id": slot_id}
    save_presets(presets)
    return _strip_api_key(presets[slot_id])


# ── AI API proxy ───────────────────────────────────────────────────────────────


class AIRequest(BaseModel):
    provider: str  # "anthropic" | "openai" | "custom"
    endpoint: str
    api_key: str
    model: str
    system: str
    messages: list[dict[str, Any]]
    max_tokens: int = 1024
    temperature: float = 1.0


@router.post("/api/ai-client")
async def ai_client(req: AIRequest):
    _validate_endpoint(req.provider, req.endpoint)
    if req.provider == "anthropic":
        headers = {
            "x-api-key": req.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": req.model,
            "max_tokens": req.max_tokens,
            "system": req.system,
            "messages": req.messages,
        }
    elif req.provider == "openai":
        headers = {
            "Authorization": f"Bearer {req.api_key}",
            "content-type": "application/json",
        }
        msgs = []
        if req.system:
            msgs.append({"role": "system", "content": req.system})
        msgs.extend(req.messages)
        body = {
            "model": req.model,
            "messages": msgs,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
        }
    else:
        # custom: pass raw body as-is
        headers = {
            "Authorization": f"Bearer {req.api_key}",
            "content-type": "application/json",
        }
        body = {
            "model": req.model,
            "messages": req.messages,
        }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(req.endpoint, headers=headers, json=body)

    return {
        "status": resp.status_code,
        "headers": dict(resp.headers),
        "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
        "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
    }
