import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import SECRET_TOKEN, SHELL
from .pty_manager import PTYSession
from . import formatter, pip_manager, api_client

app = FastAPI(title="MY Terminal")

STATIC_DIR = Path(__file__).parent / "static"

# ── Static files ───────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/manifest.json")
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")


@app.get("/sw.js")
async def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(formatter.router)
app.include_router(pip_manager.router)
app.include_router(api_client.router)


# ── PTY WebSocket ──────────────────────────────────────────────────────────────

def _check_token(token: str):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.websocket("/ws/pty")
async def pty_ws(ws: WebSocket, token: str = Query(...)):
    if token != SECRET_TOKEN:
        await ws.close(code=1008)
        return

    await ws.accept()
    session = PTYSession()

    async def send_output(data: bytes):
        try:
            await ws.send_bytes(data)
        except Exception:
            pass

    await session.start(SHELL, send_output)

    try:
        while True:
            msg = await ws.receive_json()
            msg_type = msg.get("type")
            if msg_type == "input":
                data = msg.get("data", "")
                session.write(data.encode() if isinstance(data, str) else data)
            elif msg_type == "resize":
                session.resize(int(msg.get("rows", 24)), int(msg.get("cols", 80)))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await session.kill()
