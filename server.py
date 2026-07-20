import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from sessions import (
    create_session,
    get_session,
    activate_session,
    can_create_session,
    record_message,
    sweep_idle_sessions,
)
from main import run_pipeline

# how often to clean up abandoned sessions
_SWEEP_INTERVAL_SECONDS = 300  # every 5 minutes


async def _sweep_loop():
    while True:
        await asyncio.sleep(_SWEEP_INTERVAL_SECONDS)
        try:
            # run the blocking cleanup off the event loop
            closed = await asyncio.to_thread(sweep_idle_sessions)
            if closed:
                print(f"swept {len(closed)} idle session(s)")
        except Exception as exc:
            print("sweep error:", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # start the background idle-session sweeper when the server boots
    task = asyncio.create_task(_sweep_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)

# marker dropped on the queue to signal the pipeline is finished
_DONE = object()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/sessions")
def create_session_endpoint(request: Request):
    ip = request.client.host if request.client else "unknown"
    allowed, reason = can_create_session(ip)
    if not allowed:
        if reason == "capacity":
            return JSONResponse(
                status_code=503,
                content={"detail": "The demo is at capacity, please try again later."},
            )
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many active sessions from your address."},
        )
    session = create_session(ip=ip)
    return {"session_id": session.id}


@app.get("/api/sessions/{session_id}/preview/{file_path:path}")
def preview(session_id: str, file_path: str = ""):
    session = get_session(session_id)
    if session is None:
        return Response(status_code=404)

    root = session.workspace.resolve()
    target = (session.workspace / (file_path or "index.html")).resolve()

    # same confinement as the Phase 0 file-tools fix: never serve outside the session folder
    if not target.is_relative_to(root):
        return Response(status_code=403)
    if not target.is_file():
        return Response(status_code=404)

    return FileResponse(target)


@app.websocket("/api/sessions/{session_id}/ws")
async def session_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()

    if get_session(session_id) is None:
        await websocket.send_json({"type": "error", "message": "Unknown session id"})
        await websocket.close()
        return

    loop = asyncio.get_running_loop()

    try:
        while True:
            user_input = await websocket.receive_text()

            # guardrail 2: cap messages per session
            if not record_message(session_id):
                await websocket.send_json(
                    {"type": "error", "message": "Message limit reached for this session."}
                )
                await websocket.close()
                return

            # conveyor belt carrying events from the worker thread back to the event loop
            queue: asyncio.Queue = asyncio.Queue()

            def run_in_thread():
                try:
                    # ContextVar is per-thread, so this session's workspace/index
                    # are set in the same thread that runs the pipeline
                    activate_session(session_id)
                    for event in run_pipeline(user_input):
                        loop.call_soon_threadsafe(queue.put_nowait, event)
                except Exception as exc:
                    loop.call_soon_threadsafe(
                        queue.put_nowait, {"type": "error", "message": str(exc)}
                    )
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, _DONE)

            threading.Thread(target=run_in_thread, daemon=True).start()

            while True:
                event = await queue.get()
                if event is _DONE:
                    break
                await websocket.send_json(event)
    except WebSocketDisconnect:
        pass


# serve the static frontend at the root — mounted last so /api routes match first
_FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
