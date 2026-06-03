# AI-Powered Landing Page Builder

A CLI tool that lets you create and edit landing pages using natural language. Type what you want — the system figures out the code changes and applies them.

---

## How It Works

```
CLI Input
    │
    ▼
Orchestrator (classifies intent, decomposes into sub-tasks)
    │
    ▼
Python Loop (iterates sub-tasks one at a time)
    │
    ├──→ Coder Agent (LLM + file tools via ReAct)
    │
    └──→ Reviewer Agent (reads changed files, returns pass/fail)
           Pass → re-index changed files → next sub-task
           Fail → feedback to Coder (max 3 retries)
```

**Key design rules:**
- Python controls all loops, counters, and routing — never the LLM
- LLMs only classify, reason, generate, and evaluate
- Re-indexing happens after every verified change

---

## Tech Stack

| Layer | Library |
|---|---|
| Agent orchestration | LangGraph + LangChain |
| LLM | Anthropic Claude (via `langchain-anthropic`) |
| Vector store | ChromaDB (`langchain-chroma`) |
| Embeddings | HuggingFace (`langchain-huggingface`) |
| Code parsing | tree-sitter (HTML, CSS, JS) |

---

## Project Structure

```
landing-page-builder/
├── main.py               # CLI loop
├── orchestrator.py       # Intent classification + task decomposition
├── state.py              # GlobalState schema (Pydantic)
├── agents/
│   ├── coder.py          # LLM + file tools (ReAct loop)
│   └── reviewer.py       # LLM + read_file (pass/fail evaluation)
├── tools/
│   ├── file_tools.py     # read_file, edit_file, create_file, list_files, search_files
│   └── search_tools.py   # search_codebase (vector DB)
├── indexing/
│   ├── chunker.py        # tree-sitter CST → structural chunks (Layer 1+2)
│   ├── linker.py         # cross-file linking HTML↔CSS↔JS (Layer 3)
│   ├── enricher.py       # LLM-generated chunk descriptions (Layer 4)
│   └── index_manager.py  # ChromaDB management + re-indexing
├── workspace/            # landing page files live here
└── templates/            # starter templates for new pages
```

---

## RAG Pipeline (4 Layers)

1. **Structural chunking** — tree-sitter splits HTML sections, CSS rules, JS functions
2. **Semantic grouping** — merges CSS rules sharing a base selector; merges JS handlers targeting the same DOM element
3. **Cross-file linking** — connects HTML classes/IDs to their CSS rules and JS handlers
4. **LLM enrichment** — prepends a natural-language description to each chunk before embedding

---

## State Schema

```python
class GlobalState(BaseModel):
    intent: Literal["create", "edit", "question"]
    sub_questions: list[SubQuestion]
    current_index: int
    status: list[Literal["pending", "in_progress", "done", "failed"]]
    attempt: int
    max_attempts: int = 3
    reviewer_feedback: Optional[str]
    change_log: list[dict]
    conversation_history: list[dict]
```

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your Anthropic API key
python main.py
```

---

## Build Phases

| Phase | Steps | Status |
|---|---|---|
| 1 — Foundation | Project setup, file tools, CLI loop, Coder Agent | 🔄 In progress |
| 2 — Orchestration | State schema, Orchestrator, Python loop wiring | ⏳ Pending |
| 3 — Quality | Reviewer Agent, retry loop, conversation history | ⏳ Pending |
| 4 — RAG Pipeline | tree-sitter chunking, linking, enrichment, ChromaDB | ⏳ Pending |
