# AI-Powered Landing Page Builder

A CLI tool that creates and edits production-grade landing pages from natural language.
Type what you want — *"create a landing page for a productivity app"* or *"make the hero
headline bigger"* — and a multi-agent pipeline writes, reviews, and applies the code.

It pairs a **multi-agent loop** (orchestrator → coder → reviewer, with a retry-on-failure
quality gate) with a **custom 4-layer RAG system** that lets the agents find the right code
in an existing page using semantic search over AST-aware chunks.


---

## How It Works

```
CLI Input
    │
    ▼
Orchestrator ── classifies intent (create / edit / question)
    │           and decomposes into typed sub-questions
    ▼
Pipeline Loop (main.py) ── iterates sub-questions, routes by type
    │
    ├──→ type "code"      → Coder Agent ──→ Reviewer Agent
    │                         (ReAct +        (pass/fail + feedback)
    │                          file tools)      │
    │                                           ├─ PASS → re-index changed files → next
    │                                           └─ FAIL → feedback to Coder (max 3 retries)
    │
    ├──→ type "question"  → Question Agent (ReAct: search_codebase + read_file)
    │
    └──→ type "copy"      → Copy Handler (single LLM call, no tools)
```

**Key design rules:**
- **Python controls all loops, counters, and routing** — never the LLM
- **LLMs only classify, reason, generate, and evaluate** — structured output enforces shape
- **Re-indexing happens after every verified change**, so search always reflects current code

---

## Tech Stack

| Layer | Choice |
|---|---|
| Agent runtime | LangGraph (`create_react_agent`, `MemorySaver`) + LangChain |
| LLM | Azure OpenAI (`langchain-openai` → `AzureChatOpenAI`) |
| Structured output / schemas | Pydantic (`with_structured_output`, `response_format`) |
| Vector store | ChromaDB (`PersistentClient`) |
| Embeddings | ChromaDB built-in `all-MiniLM-L6-v2` (runs locally, no API key) |
| Code parsing | tree-sitter (HTML, CSS, JS) |

---

## Project Structure

```
coding-agent/
├── main.py               # CLI entry, pipeline loop, routing, retry orchestration
├── orchestrator.py       # Intent classification + task decomposition (structured output)
├── state.py              # SubQuestion + GlobalState (Pydantic run model)
├── frontend_design.md    # Design "skill" injected into the Coder agent
├── PROJECT_PLAYBOOK.md   # Full architecture guide + interview refresher
├── agents/
│   ├── coder.py          # ReAct coder (file tools, MemorySaver thread, design injection)
│   ├── reviewer.py       # ReAct reviewer (structured pass/fail + file-scoped feedback)
│   └── handlers.py       # run_question (agent) + run_copy (plain LLM call)
├── tools/
│   └── file_tools.py     # read/create/edit/list/search_files + search_codebase
├── indexing/
│   ├── chunker.py        # Layer 1 structural chunking + Layer 2 semantic grouping
│   ├── enricher.py       # Layer 4 LLM chunk summaries (parallel via .batch())
│   └── index_manager.py  # ChromaDB store, search, and re-indexing
└── workspace/            # the generated landing page (index.html, style.css, script.js)
```

> Layer 3 (cross-file linking) was intentionally skipped — see the RAG notes below — so
> there is no `linker.py`.

---

## RAG Pipeline (Layers)

The agents need to find the right ~10 lines inside an existing page. Naive RAG splits text
every N characters and mangles code, so this pipeline is **AST-aware** and **semantics-first**.

1. **Structural chunking** (`chunker.py`) — tree-sitter parses each file and cuts chunks on
   real syntax boundaries: one chunk per CSS `rule_set`, per top-level JS statement, and per
   top-level section in `<body>`. Never mid-syntax.
2. **Semantic grouping** (`chunker.py`) — merges fragments that form one feature: CSS rules
   sharing a base selector (`.navbar`, `.navbar.scrolled`, `.navbar a`), and a JS declaration
   plus the following statements that reference it (`const navbar = …` + its scroll listener).
3. **Cross-file linking** — **skipped by design.** It would link a feature's HTML/CSS/JS via
   token matching, but Layer 4's natural-language summaries already connect them through
   *meaning* (more robust, less brittle), so this layer was never built.
4. **LLM enrichment** (`enricher.py`) — an LLM writes a one-sentence natural-language summary
   of each chunk, run in parallel with LangChain's `.batch()`.

**Storage & search** (`index_manager.py`): ChromaDB **embeds the summary** (so human queries
match) and **stores the raw code** in metadata (so the agent reads real code). Chunks use a
stable ID (`file::start::end`) with `upsert`, so re-indexing an edit updates chunks instead
of duplicating them.

> **The one-line idea:** *embed how a human would describe the code; return the actual code.*

---

## State Schema

```python
class SubQuestion(BaseModel):
    question: str
    type: Literal["code", "copy", "question"]

class GlobalState(BaseModel):
    intent: Literal["create", "edit", "question"]
    sub_questions: list[SubQuestion]
    current_index: int = 0
    status: list[Literal["pending", "in_progress", "done", "failed"]]
    attempt: int = 1
    max_attempts: int = 3
    reviewer_feedback: Optional[str] = None
    change_log: list[dict]
    conversation_history: list[dict]
```

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with your Azure OpenAI credentials:

```
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-xx-xx
AZURE_OPENAI_API_KEY=your-key
```

Then run:

```bash
python main.py
```

On first run the workspace is indexed automatically (ChromaDB also downloads the local
embedding model once, ~80MB, then caches it).

**Example prompts:**
```
create a landing page for a productivity app called "Flowly" that helps remote teams stay in sync
make the hero headline font size larger
what animations does the page use on scroll?
```

---

## Build Phases

| Phase | Scope | Status |
|---|---|---|
| 1 — Foundation | Project setup, file tools, CLI loop, Coder Agent | ✅ Done |
| 2 — Orchestration | State schema, Orchestrator, Python loop wiring, question/copy handlers | ✅ Done |
| 3 — Quality | Reviewer Agent, coder↔reviewer retry loop | ✅ Done |
| 4 — RAG Pipeline | tree-sitter chunking, semantic grouping, LLM enrichment, ChromaDB search | ✅ Done |

**Known limitations / next steps:** HTML chunking is shallow (a large `<main>` becomes one
chunk); orchestrator conversation history is parked; no automated tests yet; reviewer judges
by reading, not by running the page. See [PROJECT_PLAYBOOK.md](PROJECT_PLAYBOOK.md) §9.
```
