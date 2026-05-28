# Landing Page Builder — AI Agent

A LangGraph-powered multi-agent system that creates and edits landing pages (HTML/CSS) from natural language instructions.

> "Create a SaaS landing page for Acme with a green CTA button and testimonials section"
> → produces `output/index.html` + `output/styles.css`

---

## How It Works

```
User Instruction
      │
      ▼
┌─────────────────┐
│  Planning Agent  │  • Rewrites & enhances the query
│                  │  • Decomposes into sub-questions
│                  │  • Classifies intent
│                  │    (create_html | create_css | edit_style |
│                  │     add_section | add_functionality)
└────────┬─────────┘
         │  sub_questions[], enhanced_query, intent
         ▼
┌─────────────────┐
│  Router Node    │  • Sets idx = 0 (current sub-question pointer)
│                  │  • Tracks retry count per sub-question
│                  │  • Triggers codebase re-indexing after file changes
└────────┬─────────┘
         │  current_sub_question (sub_questions[idx])
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Manager Agent (ReAct)                    │
│                                                              │
│  Tools: read_file, list_dir                                  │
│                                                              │
│  For each sub-question, routes to one of:                    │
│                                                              │
│   ┌──────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│   │  RAG Agent   │  │ Code Gen Agent  │  │Code Edit Agent│ │
│   │              │  │                 │  │  (ReAct)      │ │
│   │ Retrieves    │  │ Generates new   │  │               │ │
│   │ relevant     │  │ HTML/CSS code   │  │ Tools:        │ │
│   │ code chunks  │  │ from scratch    │  │ edit_file     │ │
│   │ via ChromaDB │  │                 │  │ create_file   │ │
│   │              │  │                 │  │ read_file     │ │
│   │              │  │                 │  │ list_dir      │ │
│   └──────┬───────┘  └────────┬────────┘  └──────┬────────┘ │
│          └──────────────────┬┘                  │          │
└─────────────────────────────┼────────────────────┘          
                               │ generated_code, changed_files[]
                               ▼
                    ┌─────────────────┐
                    │ Validator Agent  │
                    │                  │
                    │ Receives:        │
                    │ • code changes   │
                    │ • current sub-q  │
                    │ • AST of file    │
                    │ • full context   │
                    │                  │
                    │ Returns:         │
                    │ ✅ satisfied     │
                    │ ❌ + feedback    │
                    └────────┬─────────┘
                             │
               ┌─────────────┴──────────────┐
               │                             │
          ✅ Satisfied                  ❌ Failed
               │                             │
               ▼                             ▼
        Router: idx += 1            Router: retries += 1
        Re-index codebase           Feedback → Manager
               │                   Route to relevant agent
               │                   (up to max retries)
               ▼
        ┌──────────────────┐
        │  More sub-        │
        │  questions left? │
        └──────┬─────┬─────┘
               │Yes  │No
               │     ▼
               │   output/index.html
               │   output/styles.css
               │
               ▼
        Manager Agent
        (next sub-question)
```

---

## Agent Responsibilities

| Agent | Type | Core Task | Tools |
|---|---|---|---|
| **Planning Agent** | LLM Chain | Decompose query, classify intent, rewrite query | — |
| **Manager Agent** | ReAct | Route each sub-question to the right agent | `read_file`, `list_dir` |
| **RAG Agent** | LLM + ChromaDB | Retrieve relevant code chunks semantically | ChromaDB retriever |
| **Code Gen Agent** | LLM Chain | Generate new HTML/CSS from scratch | — |
| **Code Edit Agent** | ReAct | Apply code changes to files on disk | `edit_file`, `create_file`, `read_file`, `list_dir` |
| **Validator Agent** | LLM Chain | Verify the change satisfies the sub-question | AST parser |

---

## Shared State (`graph/state.py`)

```python
{
  "query":                str,   # original user instruction
  "enhanced_query":       str,   # rewritten by planning agent
  "intent":               str,   # e.g. "create_html", "edit_style"
  "sub_questions":        list,  # decomposed steps
  "idx":                  int,   # pointer to current sub-question
  "retries":              int,   # retry count for current sub-question
  "current_sub_question": str,   # sub_questions[idx]
  "retrieved_chunks":     list,  # from RAG agent
  "generated_code":       str,   # from code gen / edit agent
  "changed_files":        list,  # files modified on disk
  "validation_feedback":  str,   # from validator if failed
  "is_done":              bool   # all sub-questions resolved
}
```

---

## RAG Pipeline

```
output/index.html
     │
     ▼
  AST Parser (BeautifulSoup4)
  Parse full HTML tree
     │
     ▼
  AST-based Chunker
  ┌─────────────────────────────────────────┐
  │  Skip <HEAD>                             │
  │  For each node in <BODY>:               │
  │    • parent node  → one Document chunk  │
  │    • each child   → one Document chunk  │
  │  Each chunk carries metadata:           │
  │    { tag, id, class, parent_tag,        │
  │      file, depth }                      │
  └─────────────────────────────────────────┘
     │  list[Document]
     ▼
  LangChain Embedder
  Chroma.from_documents(docs, embedding)
     │
     ▼
  ChromaDB (local, persistent)
     │
     ▼  ← triggered per sub-question
  Retriever  (similarity search)
     │
     ▼
  retrieved_chunks → Manager / Code Edit Agent
```

Re-indexing is triggered by the **Router** every time `changed_files` is non-empty, keeping the vector store in sync with the latest file state.

---

## Project Structure

```
coding agent/
├── agents/
│   ├── planning_agent.py      # intent classification, sub-question decomp
│   ├── manager_agent.py       # ReAct routing agent
│   ├── rag_agent.py           # ChromaDB semantic retrieval
│   ├── code_gen_agent.py      # HTML/CSS generation
│   ├── code_edit_agent.py     # ReAct file editing agent
│   └── validator_agent.py     # change validation + feedback
├── graph/
│   ├── state.py               # AgentState TypedDict
│   ├── graph.py               # LangGraph nodes + edges
│   └── router.py              # idx/retry management, re-indexing trigger
├── tools/
│   ├── file_tools.py          # read_file, create_file, edit_file, list_dir
│   └── ast_tools.py           # HTML/CSS AST parsing for validator
├── rag/
│   ├── indexer.py             # chunk + embed → ChromaDB
│   └── retriever.py           # semantic search
├── prompts/                   # system prompts per agent
├── output/                    # generated HTML + CSS files
├── main.py                    # entry point
├── requirements.txt
└── .env                       # GROQ_API_KEY
```

---

## Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM | Groq (`langchain-groq`) |
| Vector store | ChromaDB (local) |
| Embeddings | LangChain embedder via `Chroma.from_documents()` |
| HTML chunking | AST-based (parent + child nodes, with metadata) |
| HTML/CSS parsing | BeautifulSoup4 + cssutils |

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Run
python main.py "Create a SaaS landing page for Acme with a hero section, features grid, and a green CTA button"
```

Output files will be written to `output/`.
