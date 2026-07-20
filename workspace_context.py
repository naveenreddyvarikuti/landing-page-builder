from contextvars import ContextVar
from pathlib import Path

_DEFAULT_WORKSPACE = Path(__file__).parent / "workspace"

_workspace_var: ContextVar[Path] = ContextVar("workspace", default=_DEFAULT_WORKSPACE)


def get_workspace() -> Path:
    """Return the workspace folder for the current context (session)."""
    return _workspace_var.get()


def set_workspace(path: Path) -> None:
    """Set the workspace folder for the current context (session)."""
    _workspace_var.set(path)
