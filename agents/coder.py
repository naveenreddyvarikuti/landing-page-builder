from pathlib import Path
import os
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from tools.file_tools import read_file, create_file, edit_file, list_files, search_files

load_dotenv()

_design_skill = (Path(__file__).parent.parent / "frontend_design.md").read_text()

_system_prompt = """You are an expert frontend coding agent that builds and edits landing pages.
You work exclusively with HTML, CSS, and JavaScript files inside the workspace.

TOOLS:
- list_files: use this first when you don't know what files exist
- read_file: always read a file before editing it — never guess the content
- create_file: use for new files only; if the file exists, use edit_file instead
- edit_file: make surgical edits by replacing exact text; read the file first to get old_text
- search_files: use when you need to find which file contains a specific class, id, or string

RULES:
- Never fabricate file contents — always read first
- Make one edit at a time; verify the change makes sense before moving on
- Write clean, semantic HTML; use CSS classes over inline styles
- If a task needs multiple files changed, handle them one file at a time
- When creating a new page from scratch, always create index.html, style.css, and script.js

DESIGN STANDARDS:
- Dark theme by default, distinctive fonts (never Inter/Roboto/Arial), strong accent color
- Gradient text on headlines, glassmorphism cards, gradient mesh background
- Scroll-reveal animations via IntersectionObserver, smooth hover transitions
- Production-quality copy — no lorem ipsum, no placeholder text
- Every page must feel like it belongs to a funded startup"""

_tools = [read_file, create_file, edit_file, list_files, search_files]
_model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
_agent = create_react_agent(_model, _tools, prompt=_system_prompt)


def run_coder(user_message: str) -> str:
    # design skill injected as context so the model has full guidelines during creation
    content = f"{user_message}\n\n<design_guidelines>\n{_design_skill}\n</design_guidelines>"
    result = _agent.invoke({"messages": [{"role": "user", "content": content}]})
    return result["messages"][-1].content
