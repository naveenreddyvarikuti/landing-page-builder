from pathlib import Path
from langchain_core.tools import tool

WORKSPACE = Path(__file__).parent.parent / "workspace"


@tool
def read_file(path: str) -> str:
    """Read the contents of a file in the workspace. Path is relative to workspace/."""
    file = WORKSPACE / path
    if not file.exists():
        return f"Error: {path} does not exist"
    return file.read_text(encoding="utf-8")


@tool
def create_file(path: str, content: str) -> str:
    """Create a new file in the workspace with the given content. Path is relative to workspace/."""
    file = WORKSPACE / path
    if file.exists():
        return f"Error: {path} already exists. Use edit_file to modify it."
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")
    return f"Created {path}"


@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edit a file by replacing old_text with new_text. Always read the file first to get the exact text."""
    file = WORKSPACE / path
    if not file.exists():
        return f"Error: {path} does not exist"
    content = file.read_text(encoding="utf-8")
    if old_text not in content:
        return f"Error: could not find the target text in {path}"
    # replace only the first occurrence to avoid unintended changes
    file.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
    return f"Edited {path}"


@tool
def list_files() -> list[str]:
    """List all files currently in the workspace."""
    if not WORKSPACE.exists():
        return []
    return [str(f.relative_to(WORKSPACE)) for f in WORKSPACE.rglob("*") if f.is_file()]


@tool
def search_codebase(query: str) -> str:
    """Search the indexed codebase for code relevant to a query. Use this to find
    which file and lines handle a specific UI feature, component, or behaviour."""
    from indexing.index_manager import search
    hits = search(query)
    if not hits:
        return "No relevant code found."
    parts = []
    for h in hits:
        parts.append(
            f"[{h['file']} lines {h['lines']}] ({h['type']})\n"
            f"Summary: {h['summary']}\n"
            f"```\n{h['text']}\n```"
        )
    return "\n\n---\n\n".join(parts)


@tool
def search_files(query: str) -> str:
    """Search for a string across all workspace files. Returns matching lines with file path and line number."""
    results = []
    for file in WORKSPACE.rglob("*"):
        if not file.is_file():
            continue
        for i, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1):
            if query.lower() in line.lower():
                rel_path = file.relative_to(WORKSPACE)
                results.append(f"{rel_path}:{i}: {line.strip()}")
    return "\n".join(results) if results else "No matches found"
