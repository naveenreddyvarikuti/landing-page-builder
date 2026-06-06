import os
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from indexing.chunker import Chunk

load_dotenv()

_system_prompt = (
    "You help document a landing page codebase. Given a single code chunk, "
    "write one concise sentence describing what it does and what UI feature or "
    "component it belongs to. Use language a developer would use when searching "
    "for this code — focus on the UI concept (e.g. 'navbar', 'hero section', "
    "'scroll animation'), not the syntax."
)


class ChunkSummary(BaseModel):
    summary: str


_llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
).with_structured_output(ChunkSummary)


def _make_messages(chunk: Chunk) -> list:
    context = f"({chunk.type} — {chunk.file} lines {chunk.start_line}-{chunk.end_line})"
    return [
        SystemMessage(content=_system_prompt),
        HumanMessage(content=f"{context}\n{chunk.text}"),
    ]


def enrich(chunks: list[Chunk]) -> list[Chunk]:
    results = _llm.batch([_make_messages(c) for c in chunks])
    for chunk, result in zip(chunks, results):
        chunk.summary = result.summary
    return chunks
