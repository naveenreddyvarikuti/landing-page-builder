# Landing Page Builder

An AI agent that takes a plain English instruction and writes or edits landing page HTML and CSS files. You describe what you want, the agent figures out the steps, writes the code, checks its own work, and keeps going until everything is done.

Give it something like:

> "Create a SaaS landing page for Acme with a hero section, features grid, and a green CTA button"

It produces `output/index.html` and `output/styles.css`.

---

## Architecture

The system is built on LangGraph. There are five agents and a router node. Each agent has a single responsibility and they pass state through a shared object.

```
User Instruction
      |
      v
Planning Agent
  Rewrites the query into a cleaner version
  Breaks it into sub-questions
  Classifies the intent
  (create_html | create_css | edit_style | add_section | add_functionality)
      |
      v
Router Node
  Sets idx = 0 (points to the first sub-question)
  Tracks retry count
  Triggers re-indexing when files change
      |
      v  current_sub_question = sub_questions[idx]
      |
      v
Manager Agent  (ReAct)
  Tools: read_file, list_dir
  Reads the codebase to understand context
  Decides which agent to call for the current sub-question
      |
      +------------------+------------------+
      |                  |                  |
      v                  v                  v
  RAG Agent        Code Gen Agent     Code Edit Agent  (ReAct)
  Searches the     Writes new         Tools: edit_file, create_file,
  codebase via     HTML/CSS           read_file, list_dir
  ChromaDB         from scratch       Applies changes to files on disk
      |                  |                  |
      +------------------+------------------+
                         |
                         v
                   Validator Agent
                   Gets: code changes, current sub-question, AST of changed file
                   Returns: satisfied or failed + feedback
                         |
              +----------+----------+
              |                     |
         Satisfied               Failed
              |                     |
              v                     v
        Router: idx += 1      Router: retries += 1
        Re-index codebase     Send feedback back to Manager
              |
        More sub-questions?
              |
         Yes  |  No
              |   v
              |  output/index.html
              |  output/styles.css
              v
        Manager Agent
        (works on next sub-question)
```

---

## What Each Agent Does

| Agent | Type | Responsibility | Tools |
|---|---|---|---|
| Planning Agent | LLM Chain | Decomposes the query, classifies intent, rewrites it | none |
| Manager Agent | ReAct | Reads codebase context, routes to the right agent | read_file, list_dir |
| RAG Agent | LLM + ChromaDB | Finds relevant code chunks for the current sub-question | ChromaDB retriever |
| Code Gen Agent | LLM Chain | Generates HTML/CSS when nothing exists yet | none |
| Code Edit Agent | ReAct | Edits or creates files on disk | edit_file, create_file, read_file, list_dir |
| Validator Agent | LLM Chain | Checks whether the change actually solves the sub-question | AST parser |

---

## Shared State

Every node reads from and writes to a single `AgentState` object. This is what flows through the graph.

```python
{
  "query":                str,   # original instruction from the user
  "enhanced_query":       str,   # cleaned up version from the planning agent
  "intent":               str,   # e.g. "create_html", "edit_style"
  "sub_questions":        list,  # the decomposed steps to solve
  "idx":                  int,   # which sub-question we are on right now
  "retries":              int,   # how many times we have retried this sub-question
  "current_sub_question": str,   # sub_questions[idx]
  "retrieved_chunks":     list,  # code chunks from the RAG agent
  "generated_code":       str,   # code produced by the gen or edit agent
  "changed_files":        list,  # files written to disk this round
  "validation_feedback":  str,   # reason if validator says failed
  "is_done":              bool   # true when all sub-questions are resolved
}
```

---

## RAG Pipeline

The RAG agent does not chunk by character count or token limit. It parses the HTML as an AST and turns each node into its own document so the retrieval is structurally aware.

```
output/index.html
      |
      v
AST Parser (BeautifulSoup4)
      |
      v
AST Chunker
  Skips <head>
  Walks <body> tree
  Each parent node becomes one Document
  Each child node becomes one Document
  Metadata per chunk: tag, id, class, parent_tag, file, depth, line number
      |  list[Document]
      v
LangChain Embedder
  Chroma.from_documents(docs, embedding)
      |
      v
ChromaDB  (local, persistent)
      |
      v  similarity search triggered per sub-question
Retriever
      |
      v
retrieved_chunks  passed to Manager and Code Edit Agent
```

The Router triggers a full re-index every time `changed_files` is non-empty, so the vector store always reflects the current state of the output files.

---

## Project Structure

```
coding agent/
  agents/
    planning_agent.py      intent classification and sub-question decomposition
    manager_agent.py       ReAct routing agent
    rag_agent.py           ChromaDB semantic retrieval
    code_gen_agent.py      HTML/CSS generation from scratch
    code_edit_agent.py     ReAct file editing agent
    validator_agent.py     change validation and feedback
  graph/
    state.py               AgentState TypedDict
    graph.py               LangGraph nodes and edges
    router.py              idx and retry management, re-indexing trigger
  tools/
    file_tools.py          read_file, create_file, edit_file, list_dir
    ast_tools.py           HTML/CSS AST parsing for the validator
  rag/
    indexer.py             AST chunker and Chroma.from_documents ingestion
    retriever.py           similarity search over the vector store
  prompts/                 system prompts, one file per agent
  output/                  generated HTML and CSS land here
  main.py                  entry point
  requirements.txt
  .env                     GROQ_API_KEY
```

---

## Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM | Groq via langchain-groq |
| Vector store | ChromaDB local |
| Embeddings | LangChain embedder, Chroma.from_documents |
| HTML chunking | AST-based, parent and child nodes with metadata |
| HTML/CSS parsing | BeautifulSoup4 and cssutils |

---

## Getting Started

Install dependencies:

```bash
pip install -r requirements.txt
```

Add your Groq API key to `.env`:

```
GROQ_API_KEY=your_key_here
```

Run it:

```bash
python main.py "Create a SaaS landing page for Acme with a hero section, features grid, and a green CTA button"
```

Output is written to the `output/` folder.
