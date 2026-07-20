import shutil
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from workspace_context import set_workspace
from indexing.index_manager import set_collection_name, drop_collection

SESSIONS_ROOT = Path(__file__).parent / "session_workspaces"

# abuse guardrails
MAX_MESSAGES_PER_SESSION = 20
MAX_SESSIONS_PER_IP = 5
MAX_SESSIONS_PER_DAY = 200


@dataclass
class Session:
    id: str
    workspace: Path | None = None
    collection_name: str | None = None
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0
    ip: str | None = None


_sessions: dict[str, Session] = {}

# rolling daily counter of sessions created (guardrail 4)
_daily_count = 0
_daily_date: date | None = None


def _roll_daily_if_needed() -> None:
    """Reset the daily session counter when the calendar day (UTC) changes."""
    global _daily_count, _daily_date
    today = datetime.now(timezone.utc).date()
    if _daily_date != today:
        _daily_date = today
        _daily_count = 0


def create_session(ip: str | None = None) -> Session:
    """Create a new session: a real empty workspace folder and a dedicated search index name."""
    global _daily_count
    _roll_daily_if_needed()
    _daily_count += 1
    session_id = str(uuid.uuid4())
    workspace = SESSIONS_ROOT / session_id
    workspace.mkdir(parents=True, exist_ok=True)
    session = Session(
        id=session_id,
        workspace=workspace,
        collection_name=f"codebase_{session_id}",
        ip=ip,
    )
    _sessions[session_id] = session
    return session


def count_sessions_for_ip(ip: str) -> int:
    """How many active sessions currently belong to this IP address."""
    return sum(1 for s in _sessions.values() if s.ip == ip)


def at_daily_capacity() -> bool:
    """True once today's session-creation count has hit the daily limit."""
    _roll_daily_if_needed()
    return _daily_count >= MAX_SESSIONS_PER_DAY


def can_create_session(ip: str) -> tuple[bool, str | None]:
    """Admission check. Returns (allowed, reason). reason is 'capacity' or 'ip_limit' when denied."""
    if at_daily_capacity():
        return False, "capacity"
    if count_sessions_for_ip(ip) >= MAX_SESSIONS_PER_IP:
        return False, "ip_limit"
    return True, None


def record_message(session_id: str) -> bool:
    """Count one message against a session. Returns False once it exceeds the per-session limit."""
    session = _sessions.get(session_id)
    if session is None:
        return False
    session.message_count += 1
    return session.message_count <= MAX_MESSAGES_PER_SESSION


def get_session(session_id: str) -> Session | None:
    """Look up a session by ID. Returns None if it doesn't exist."""
    return _sessions.get(session_id)


def touch_session(session_id: str) -> None:
    """Mark a session as active just now, resetting its idle timer."""
    session = _sessions.get(session_id)
    if session is not None:
        session.last_active = datetime.now(timezone.utc)


def list_sessions() -> list[Session]:
    """Return all currently active sessions."""
    return list(_sessions.values())


def activate_session(session_id: str) -> Session:
    """Point the active workspace and search index at the given session."""
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Unknown session id: {session_id}")
    touch_session(session_id)
    set_workspace(session.workspace)
    set_collection_name(session.collection_name)
    return session


def close_session(session_id: str) -> None:
    """Delete a session's workspace folder and search index, and forget about it.
    Safe to call on an already-closed or unknown session id."""
    session = _sessions.pop(session_id, None)
    if session is None:
        return
    shutil.rmtree(session.workspace, ignore_errors=True)
    drop_collection(session.collection_name)


def sweep_idle_sessions(idle_minutes: int = 30) -> list[str]:
    """Close every session idle for longer than idle_minutes. Returns the ids that were closed."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=idle_minutes)
    idle_ids = [s.id for s in list_sessions() if s.last_active < cutoff]
    for session_id in idle_ids:
        close_session(session_id)
    return idle_ids
