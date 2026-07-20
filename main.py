import uuid
import warnings

# structured output adds a harmless `parsed` field that trips Pydantic's serializer warning
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

from orchestrator import run_orchestrator
from agents.coder import run_coder
from agents.reviewer import run_reviewer
from agents.handlers import run_question, run_copy
from state import GlobalState, SubQuestion
from indexing.index_manager import index_workspace, index_file, is_empty


def handle_code_task(state: GlobalState, sq: SubQuestion):
    """Yields structured events for each step. Returns True/False for overall success
    (retrieve via `ok = yield from handle_code_task(...)`)."""
    # one thread per sub-question so retries share conversation history
    thread_id = str(uuid.uuid4())
    feedback = None

    while state.attempt <= state.max_attempts:
        summary, changed = run_coder(sq.question, thread_id, feedback)
        yield {"type": "coder_step", "summary": summary}

        if not changed:
            # nothing was written — nothing to review
            return True

        review = run_reviewer(sq.question, changed)
        state.change_log.append({
            "task": sq.question,
            "files": changed,
            "attempt": state.attempt,
            "passed": review.passed,
        })

        if review.passed:
            yield {"type": "review", "passed": True, "feedback": review.feedback}
            for f in changed:
                index_file(f)
            return True

        yield {"type": "review", "passed": False, "feedback": review.feedback, "attempt": state.attempt}
        feedback = review.feedback
        state.reviewer_feedback = review.feedback
        state.attempt += 1

    return False


def run_pipeline(user_input: str):
    """Yields structured events describing pipeline progress."""
    state = run_orchestrator(user_input)
    yield {"type": "orchestrator", "intent": state.intent, "tasks": len(state.sub_questions)}

    if is_empty():
        yield {"type": "indexing_start"}
        index_workspace()

    while not state.is_done():
        sq = state.current_sub_question()
        idx, total = state.current_index + 1, len(state.sub_questions)
        yield {"type": "task_start", "index": idx, "total": total, "task_type": sq.type, "question": sq.question}

        if sq.type == "code":
            ok = yield from handle_code_task(state, sq)
            if ok:
                state.advance()
            else:
                yield {"type": "task_failed", "question": sq.question}
                state.mark_failed()
        elif sq.type == "copy":
            result = run_copy(sq.question)
            yield {"type": "copy_result", "result": result}
            state.advance()
        else:
            result = run_question(sq.question)
            yield {"type": "question_result", "result": result}
            state.advance()

    yield {"type": "done"}


def print_event(event: dict) -> None:
    etype = event["type"]
    if etype == "orchestrator":
        print(f"\nIntent: {event['intent']} | Tasks: {event['tasks']}\n")
    elif etype == "indexing_start":
        print("Indexing workspace...")
    elif etype == "task_start":
        print(f"[{event['index']}/{event['total']}] ({event['task_type']}) {event['question']}")
    elif etype == "coder_step":
        print(f"  coder: {event['summary']}")
    elif etype == "review":
        if event["passed"]:
            print(f"  review: PASS — {event['feedback']}")
        else:
            print(f"  review: FAIL (attempt {event['attempt']}) — {event['feedback']}")
    elif etype == "task_failed":
        print("  giving up after max attempts.")
    elif etype in ("copy_result", "question_result"):
        print(f"  → {event['result']}")
    elif etype == "done":
        print("\nDone.\n")


def main():
    print("Landing Page Builder")
    print("Type your instruction or 'exit' to quit.\n")

    while True:
        user_input = input("> ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        for event in run_pipeline(user_input):
            print_event(event)


if __name__ == "__main__":
    main()
