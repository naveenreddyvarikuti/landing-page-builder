import os
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from tools.file_tools import read_file, list_files

load_dotenv()


class ReviewResult(BaseModel):
    passed: bool
    feedback: str
    files_reviewed: list[str]


_prompt = """You are a strict code reviewer for landing page edits.
You are given the task that was requested and the list of files that were changed.
Read those files and judge whether the change correctly and completely satisfies the task.

Rules:
- Review ONLY the changed files you are told about — read each one before judging.
- Your feedback MUST reference specific file names (e.g. "In style.css, ...").
- If the change is correct and complete, set passed=true with a short confirmation.
- If anything is wrong, missing, or low quality, set passed=false and explain exactly
  what to fix and in which file. Be specific and actionable — the coder retries from this."""

_model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
_agent = create_react_agent(
    _model, [read_file, list_files], prompt=_prompt, response_format=ReviewResult
)


def run_reviewer(task: str, changed_files: list[str]) -> ReviewResult:
    files = ", ".join(changed_files) if changed_files else "none"
    message = f"Task: {task}\n\nChanged files to review: {files}"
    result = _agent.invoke({"messages": [{"role": "user", "content": message}]})
    return result["structured_response"]
