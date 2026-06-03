import uuid
import warnings

# structured output adds a harmless `parsed` field that trips Pydantic's serializer warning
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

from orchestrator import run_orchestrator
from agents.coder import run_coder
from agents.reviewer import run_reviewer
from agents.handlers import run_question, run_copy
from state import GlobalState, SubQuestion


def handle_code_task(state: GlobalState, sq: SubQuestion) -> bool:
    # one thread per sub-question so retries share conversation history
    thread_id = str(uuid.uuid4())
    feedback = None

    while state.attempt <= state.max_attempts:
        summary, changed = run_coder(sq.question, thread_id, feedback)
        print(f"  coder: {summary}")

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
            print(f"  review: PASS — {review.feedback}")
            return True

        print(f"  review: FAIL (attempt {state.attempt}) — {review.feedback}")
        feedback = review.feedback
        state.reviewer_feedback = review.feedback
        state.attempt += 1

    return False


def run_pipeline(user_input: str) -> None:
    state = run_orchestrator(user_input)
    print(f"\nIntent: {state.intent} | Tasks: {len(state.sub_questions)}\n")

    while not state.is_done():
        sq = state.current_sub_question()
        idx, total = state.current_index + 1, len(state.sub_questions)
        print(f"[{idx}/{total}] ({sq.type}) {sq.question}")

        if sq.type == "code":
            ok = handle_code_task(state, sq)
            if ok:
                state.advance()
            else:
                print("  giving up after max attempts.")
                state.mark_failed()
        elif sq.type == "copy":
            print(f"  → {run_copy(sq.question)}")
            state.advance()
        else:
            print(f"  → {run_question(sq.question)}")
            state.advance()

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

        run_pipeline(user_input)


if __name__ == "__main__":
    main()
