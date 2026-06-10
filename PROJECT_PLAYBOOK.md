# Flowly Builder — Project Playbook & Interview Guide

> An AI-powered CLI tool that builds and edits production-grade landing pages from
> natural-language instructions, using a multi-agent pipeline and a custom 4-layer
> RAG system for code retrieval.

This document is your **interview refresher**. It explains *what* you built, *how* the
pieces fit, and — most importantly — *why* you made each decision. Interviewers care far
more about the "why" than the "what".

---

## 1. The 30-Second Elevator Pitch

> "I built a CLI coding agent that turns plain-English requests like *'create a landing
> page for a productivity app'* or *'make the hero headline bigger'* into real HTML/CSS/JS
> files. It uses a **multi-agent architecture** — an orchestrator classifies intent and
> splits work, a coder agent writes code using tools, and a reviewer agent grades the
> output and sends feedback for retries. To let the agents *find* relevant code in an
> existing page, I built a **custom RAG pipeline** that parses code with tree-sitter,
> groups related pieces, has an LLM describe each piece in plain English, and stores it
> all in a vector database for semantic search."

**Three things that make it interesting to talk about:**
1. **Multi-agent loop with a quality gate** (coder ↔ reviewer, max 3 retries)
2. **Custom RAG over *code*** (not documents) — AST-aware chunking, not naive text splitting
3. **The "LLM as a semantic bridge"** insight — describing code in natural language so it
   matches natural-language queries

---

## 2. The Big Picture (Architecture Diagram)

```
                            ┌─────────────────────┐
                            │   CLI (main.py)     │
                            │  "create a page..." │
                            └──────────┬──────────┘
                                       │ user_input
                                       ▼
                            ┌─────────────────────┐
                            │   ORCHESTRATOR      │   LLM with structured output
                            │  (orchestrator.py)  │   → intent + sub_questions[]
                            └──────────┬──────────┘
                                       │ GlobalState
                                       ▼
                            ┌─────────────────────┐
                            │  PIPELINE LOOP      │   walks each sub-question,
                            │  (main.py)          │   routes by .type
                            └──────────┬──────────┘
                 ┌─────────────────────┼─────────────────────┐
            type=="code"          type=="question"       type=="copy"
                 │                     │                     │
                 ▼                     ▼                     ▼
        ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
        │  CODER AGENT   │    │ QUESTION AGENT │    │  COPY HANDLER  │
        │  (coder.py)    │    │ (handlers.py)  │    │ (handlers.py)  │
        │  ReAct + tools │    │ ReAct + tools  │    │ plain LLM call │
        └───────┬────────┘    └───────┬────────┘    └────────────────┘
                │ writes files        │ reads/searches
                ▼                     │
        ┌────────────────┐           │
        │ REVIEWER AGENT │           │
        │ (reviewer.py)  │           │
        │ pass/fail +    │           │
        │ feedback       │           │
        └───────┬────────┘           │
                │ FAIL → retry (≤3)   │
                │ PASS → re-index     │
                ▼                     ▼
        ┌─────────────────────────────────────────┐
        │            RAG PIPELINE                   │
        │  chunker → enricher → ChromaDB            │
        │  (indexing/)                              │
        └─────────────────────────────────────────┘
                ▲                     │
                │ search_codebase     │ index_file
                └─────────────────────┘
                   (tools/file_tools.py)
```

**The two halves of the system:**
- **The agent layer** (orchestrator, coder, reviewer, handlers) — decides *what to do* and *does it*
- **The RAG layer** (chunker, enricher, index_manager) — lets agents *find* relevant code

They connect through one tool: `search_codebase`.

---

## 3. End-to-End Walkthrough (follow a single request)

**Request:** `"make the hero headline font size larger"`

| # | Step | File | What happens |
|---|------|------|--------------|
| 1 | **Classify** | `orchestrator.py` | LLM returns `intent="edit"`, one sub-question `{type:"code", question:"make the hero headline font size larger"}` |
| 2 | **Build state** | `state.py` | Wrapped in a `GlobalState` (tracks progress, attempts, feedback) |
| 3 | **Index check** | `main.py` | If the vector DB is empty, index the whole workspace first |
| 4 | **Route** | `main.py` | `type=="code"` → `handle_code_task()` |
| 5 | **Locate code** | `coder.py` → `search_codebase("hero headline font size")` | RAG returns the `.hero h1` CSS chunk with its file + line numbers |
| 6 | **Edit** | `coder.py` → `read_file` then `edit_file` | Surgically replaces the `font-size` value |
| 7 | **Review** | `reviewer.py` | Reads the changed file, judges: did it satisfy the task? Returns `passed` + `feedback` |
| 8a | **PASS** | `main.py` | Re-index the changed file so the DB reflects the new code → advance |
| 8b | **FAIL** | `main.py` | Send feedback back to coder, retry (same conversation thread), up to 3× |
| 9 | **Done** | `main.py` | Loop ends when all sub-questions are `done` or `failed` |

---

## 4. Component Deep-Dives

### 4.1 Orchestrator — *"What does the user want?"*
**File:** `orchestrator.py`

- Single LLM call using **`with_structured_output(OrchestratorOutput)`** — guarantees the
  response is valid `{intent, sub_questions[]}`, no parsing fragile text.
- **Two jobs:** (1) classify overall `intent` (create / edit / question), (2) decompose
  into typed sub-questions.
- **Three sub-question types:**
  - `code` — ANY change that appears on the page (incl. text edits like a new headline)
  - `copy` — ONLY standalone text suggestions returned to the user, *not* applied
  - `question` — user just wants an answer, no changes
- **Key design lesson learned:** the prompt has explicit **anti-over-decomposition rules**.
  Early on, "create a landing page" got split into 1 code + 3 disconnected copy tasks,
  producing inconsistent content. Fix: *"'Create a page for X' is ONE code task."*

> **Interview soundbite:** "Structured output turns an unreliable text response into a typed
> contract — the rest of my pipeline can trust the shape of the data."

---

### 4.2 State — *"Where are we in the work?"*
**File:** `state.py`

Two Pydantic models:
- **`SubQuestion`** — `{question, type}`
- **`GlobalState`** — the full run: the list of sub-questions, `current_index`, per-task
  `status[]`, `attempt`/`max_attempts` (retry budget), `reviewer_feedback`, and a
  `change_log`.

Helper methods keep the loop clean: `current_sub_question()`, `is_done()`, `advance()`
(mark done, reset attempt counter, move on), `mark_failed()` (gave up after retries).

> **Why a state object?** It separates "what's the plan and progress" (data) from "how do
> we execute it" (the loop in main.py). Classic state-machine pattern.

---

### 4.3 Coder Agent — *"Write the code."*
**File:** `coder.py`

- Built with **`create_react_agent`** (LangGraph) — a ReAct loop: the LLM **reasons**,
  **acts** (calls a tool), **observes** the result, repeats until done.
- **Tools:** `search_codebase`, `read_file`, `create_file`, `edit_file`, `list_files`, `search_files`
- **`MemorySaver` checkpointer + `thread_id`** — each sub-question gets its own conversation
  thread. On a retry, the coder *remembers* its previous attempt; we only send the new
  reviewer feedback, not the whole task again.
- **Injects `frontend_design.md`** as `<design_guidelines>` — a "skill file" with the
  production-quality design system (dark theme, distinctive fonts, glassmorphism, etc.).
- **`_changed_files()`** — parses the message history's `tool_calls` to detect which files
  the agent created/edited. This is how we know what to send to the reviewer + re-index.

> **Interview soundbite:** "I used a per-task conversation thread so retries are a
> *continuation*, not a restart — the agent has full context of what it already tried."

---

### 4.4 Reviewer Agent — *"Is the code actually good?"*
**File:** `reviewer.py`

- Also a `create_react_agent`, but with **`response_format=ReviewResult`** → returns a typed
  `{passed: bool, feedback: str, files_reviewed: []}`.
- **Only reads the changed files** (not the whole workspace) — focused, cheaper, and
  feedback is file-scoped ("In style.css, ...") so the coder knows exactly where to fix.
- This is the **quality gate**. The coder↔reviewer loop is the core reliability mechanism.

> **Why a separate reviewer?** Same reason humans do code review — the writer is biased
> toward thinking their work is done. A fresh agent with a "strict reviewer" prompt catches
> incomplete or low-quality changes. Max 3 retries prevents infinite loops.

---

### 4.5 Handlers — *"Answer questions, write standalone copy."*
**File:** `handlers.py`

- **`run_question`** — ReAct agent with `search_codebase`, `read_file`, `list_files`. Finds
  relevant code by concept, answers from the actual files.
- **`run_copy`** — a plain single LLM call (no tools, no loop). Cheapest path — it's just
  "write me some text."

> **Design point:** not everything needs an agent. Copywriting is a one-shot task, so it
> gets a one-shot call. Match the tool to the job's complexity.

---

## 5. The RAG Pipeline (the star of the show)

> **The problem RAG solves here:** when editing an *existing* page, the agent needs to find
> the right ~10 lines among hundreds. Dumping the whole file into the prompt is wasteful and
> imprecise. RAG retrieves *just the relevant chunk*.

### Why naive RAG fails on code
Standard RAG splits documents every ~500 characters. On code that's a disaster — it cuts a
CSS rule in half, separates a function's signature from its body. **Code has structure;
chunking must respect it.** That's why I built a custom, AST-aware pipeline.

### The 4-Layer Pipeline

```
   raw file
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│ LAYER 1: STRUCTURAL CHUNKING            (chunker.py)           │
│ Parse with tree-sitter → split on real syntax boundaries      │
│   CSS  → one chunk per rule_set                                │
│   JS   → one chunk per top-level statement                    │
│   HTML → one chunk per top-level section in <body>            │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ LAYER 2: SEMANTIC GROUPING              (chunker.py)           │
│ Merge fragments that belong to the same feature               │
│   CSS  → .navbar + .navbar.scrolled + .navbar a → one chunk    │
│   JS   → `const navbar=...` + the listener that uses `navbar`  │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ LAYER 3: CROSS-FILE LINKING             (SKIPPED — see below)  │
│ Would link the navbar's HTML+CSS+JS across files.             │
│ Decided Layer 4 covers this more elegantly.                   │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ LAYER 4: LLM ENRICHMENT                 (enricher.py)          │
│ Ask an LLM to describe each chunk in plain English.           │
│ ".navbar{position:fixed...}" → "the sticky navigation bar's   │
│  frosted-glass background and scrolled state"                 │
│ Runs in PARALLEL via .batch()                                 │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ STORAGE & SEARCH                        (index_manager.py)     │
│ ChromaDB: embed the SUMMARY, store the raw CODE in metadata.   │
│ Search a natural-language query → return code + location.     │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1 — Structural chunking (tree-sitter)
- **tree-sitter** parses source into a syntax tree. I walk the tree and cut chunks on real
  node boundaries (`rule_set`, top-level statements, `<body>` sections) — never mid-syntax.
- Each `Chunk` carries `file`, `type`, `text`, `start_line`, `end_line`.

> **Key term — CST vs AST:** tree-sitter produces a *Concrete* Syntax Tree (includes every
> token, even punctuation). I filter to `is_named` nodes to drop noise like `;` and `{`.

### Layer 2 — Semantic grouping
- **The orphaned-chunk problem:** `const navbar = ...` and the scroll listener that *uses*
  `navbar` came out as two separate chunks — but they're one feature. If search returns only
  one, the agent gets half the picture.
- **CSS grouping:** merge consecutive rules sharing a *base selector* (`.navbar`).
- **JS grouping:** merge a declaration with the following statements that *reference its
  name* by word.
- **Result on the real test:** JS went 7→4 chunks, CSS 55→35 — fragments became coherent
  feature units.

### Layer 3 — Why I SKIPPED it (a maturity signal in interviews)
- Layer 3 would link the *same feature across files* (navbar's HTML `class="navbar"`, CSS
  `.navbar`, JS `'.navbar'`) by matching identical tokens.
- I realized **Layer 4 already solves this, better.** Token-matching is brittle (it misses
  "primary header" ↔ `.navbar`). LLM descriptions bridge files through *meaning*: the CSS
  and JS chunks both get summaries mentioning "navbar", so they cluster in embedding space
  naturally. **Less code, less brittle, more robust.**

> **Interview soundbite:** "I cut a planned layer because a later layer subsumed it. Knowing
> what *not* to build is as important as building it."

### Layer 4 — LLM enrichment (the key insight)
- **The core idea:** code and the queries people type are written in *different languages*.
  A user searches "fix the hero animation"; the code says `addEventListener('DOMContentLoaded')`.
  They share almost no words, so embedding the *raw code* matches the query poorly.
- **The fix:** have an LLM write a natural-language summary of each chunk. Now the summary
  ("animates the hero section's elements on page load") shares vocabulary with the query.
  **The LLM is a semantic bridge between code-language and human-language.**
- **Batching:** I use LangChain's **`.batch()`** to run all chunk descriptions as parallel
  calls. One chunk per call → results map back by position → no alignment bugs. (We
  considered one-big-prompt batching but it risked the LLM returning the wrong number of
  summaries; per-chunk parallel calls are simpler *and* safer.)

### Storage & Search — ChromaDB
- **What gets embedded:** the **summary** (natural language → matches queries).
- **What gets stored alongside:** file, type, line range, and the **raw code text** in
  metadata (this is what the agent actually reads).
- **`upsert` by a stable ID** (`file::start::end`) → re-indexing after an edit *updates*
  chunks instead of duplicating them.
- **Embedding model:** ChromaDB's built-in `all-MiniLM-L6-v2` runs locally — no API key, no
  per-embedding cost.

> **The one-line summary of the whole RAG design:**
> *"Embed how a human would describe the code; return the actual code."*

---

## 6. Tech Stack & Why Each Choice

| Tool | Role | Why |
|------|------|-----|
| **LangGraph** (`create_react_agent`, `MemorySaver`) | Agent runtime + memory | Battle-tested ReAct loop + checkpointing; I don't reinvent the agent loop |
| **LangChain** (`with_structured_output`, `.batch()`, `@tool`) | LLM plumbing | Structured output for reliability; batch for parallelism |
| **Azure OpenAI** (GPT) | The LLM | (Migrated here from Groq — see §8) |
| **Pydantic** | Typed schemas | Turns LLM output into validated objects; the "contract" everywhere |
| **tree-sitter** | Code parsing | Real AST-aware chunking instead of naive text splits |
| **ChromaDB** | Vector store | Embedded, zero-setup, local embeddings, persistent |

---

## 7. The Coder ↔ Reviewer Retry Loop (draw this if asked)

```
        ┌──────────────────────────────────────────┐
        │  thread_id = uuid()   attempt = 1         │
        └────────────────────┬─────────────────────┘
                             ▼
        ┌──────────────────────────────────────────┐
   ┌───▶│  run_coder(task, thread_id, feedback)    │
   │    │  → writes files, returns changed[]        │
   │    └────────────────────┬─────────────────────┘
   │                         │ changed files?
   │                  no ────┴──── yes
   │                  │             │
   │            (done, nothing      ▼
   │             to review)  ┌──────────────────────┐
   │                         │ run_reviewer(changed) │
   │                         │ → passed?, feedback   │
   │                         └──────────┬───────────┘
   │            FAIL & attempt<3        │ PASS
   │   feedback=review.feedback         ▼
   └── attempt += 1            ┌──────────────────────┐
                               │ re-index changed files│
                               │ advance to next task   │
                               └────────────────────────┘
```

The **`thread_id`** is the trick: because the coder shares one conversation thread across
retries, on attempt #2 we send *only* the feedback — the agent already remembers attempt #1.

---

## 8. War Stories (great for "tell me about a hard bug")

1. **Groq couldn't handle large tool-call payloads.** Generating a full HTML page produced
   huge tool-call arguments that broke Groq's JSON parsing across multiple models. **Fix:**
   migrated the whole stack to Azure OpenAI. *Lesson: provider limits are real architectural
   constraints.*
2. **Misclassification bug.** "Change the hero heading" got classified as `copy` (printed but
   never applied to the page). **Fix:** rewrote the orchestrator prompt to define `code` =
   anything that appears on the page, incl. text. *Lesson: prompt ambiguity = real bugs.*
3. **Over-decomposition.** "Create a landing page" got split into 4 disconnected tasks with
   inconsistent content. **Fix:** explicit anti-over-decomposition rules.
4. **`.env` got committed and GitHub blocked the push** (secret scanning). *Lesson:
   `.gitignore` only ignores **untracked** files — a file already tracked stays tracked. Had
   to `git rm --cached` and rotate keys.*
5. **JS chunker returned 0 chunks.** Real landing-page JS has no `function_declaration` nodes
   (it uses `const`/arrow functions/listeners). **Fix:** chunk on top-level *named statements*
   instead. *Lesson: validate assumptions against real data.*

---

## 9. Known Limitations & "What I'd Do Next" (shows maturity)

- **HTML chunking is shallow** — a big `<main>` swallowing many sections becomes one large
  chunk. Deliberately kept simple for scope; the fix is recursive section-wise chunking.
- **Conversation history across requests** isn't wired into the orchestrator (parked).
- **No tests / CI yet** — would add unit tests for the chunker/grouper (pure functions, easy
  to test) and integration tests for the pipeline.
- **Single workspace, HTML/CSS/JS only** — the chunker is language-specific; adding React/Vue
  means new tree-sitter grammars + chunk rules.
- **Reviewer can't run the code** — it judges by reading. Next step: a headless-browser smoke
  test in the loop.

---

## 10. Likely Interview Questions (with crisp answers)

**Q: Why multiple agents instead of one big prompt?**
A: Separation of concerns + a quality gate. The orchestrator plans, the coder executes, the
reviewer verifies. A single prompt has no independent check on its own work; the
coder↔reviewer loop gives me reliability through retries.

**Q: How is your RAG different from standard document RAG?**
A: Standard RAG splits text every N characters, which mangles code. I chunk on the AST with
tree-sitter (never mid-syntax), group fragments into feature units, and — the key part —
embed an *LLM-generated natural-language summary* of each chunk rather than the raw code, so
human queries actually match.

**Q: Why embed the summary and not the code?**
A: Queries and code use different vocabularies. "Fix the hero animation" shares no words with
`addEventListener('DOMContentLoaded')`. The summary bridges that gap, so semantic search
works. I still store and return the raw code — I just *search* on the description.

**Q: How do you avoid duplicate chunks when re-indexing?**
A: Stable IDs (`file::start_line::end_line`) + `upsert`. Re-indexing an edited file updates
existing chunks instead of inserting new ones.

**Q: What stops the retry loop from running forever?**
A: A `max_attempts` budget (3) in the state object. After that the task is marked `failed`
and the pipeline moves on.

**Q: Why did you skip Layer 3?**
A: It would link features across files via token matching, but Layer 4's LLM summaries already
create that linkage through shared meaning — and more robustly. Skipping it removed brittle
code without losing capability.

---

## 11. File Map (where everything lives)

```
main.py              — CLI entry, pipeline loop, routing, retry orchestration
orchestrator.py      — intent classification + task decomposition (structured output)
state.py             — SubQuestion + GlobalState (the run's data model)
frontend_design.md   — the design "skill" injected into the coder
agents/
  coder.py           — ReAct coder agent (+ MemorySaver, design injection, changed-file detection)
  reviewer.py        — ReAct reviewer agent (structured pass/fail + feedback)
  handlers.py        — run_question (agent) + run_copy (plain call)
tools/
  file_tools.py      — read/create/edit/list/search_files + search_codebase
indexing/
  chunker.py         — Layer 1 (structural) + Layer 2 (grouping)
  enricher.py        — Layer 4 (LLM summaries via .batch())
  index_manager.py   — ChromaDB store + search + re-index
                       (Layer 3 / linker.py intentionally skipped — no file)
workspace/           — the generated landing page (index.html, style.css, script.js)
```

---

*Tip: before an interview, re-draw the §2 architecture diagram and the §7 retry loop from
memory. If you can sketch those two and explain the §5 "embed the summary, return the code"
insight, you own this project.*
