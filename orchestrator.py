import os
from typing import Literal
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from state import GlobalState, SubQuestion

load_dotenv()


class OrchestratorOutput(BaseModel):
    intent: Literal["create", "edit", "question"]
    sub_questions: list[SubQuestion]


_prompt = """You are an orchestrator for an AI landing page builder.

Given a user message, do two things:

1. Classify the overall intent:
   - "create": user wants to build a new page from scratch
   - "edit": user wants to modify an existing page
   - "question": user is only asking about the page (no changes needed)

2. Decompose the message into sub-questions, each with a type:
   - "code": ANY change to the page or files — including text changes like editing a
     heading, rewriting a section, or changing a button label. If the result should
     appear on the page, it is "code". The coder writes any needed copy itself.
   - "copy": ONLY when the user explicitly wants text suggestions returned to them and
     NOT applied to the page (e.g. "suggest 3 taglines", "give me headline ideas").
   - "question": user wants to read the page and get an answer (no changes).

Decomposition rules:
- Do NOT over-split. "Create a landing page for X" is ONE "code" task — the coder builds
  the whole page (structure AND copy) in a single task. Never split a single page build
  into separate copy tasks.
- Only create multiple sub-questions when the user genuinely asks for distinct things
  (e.g. "add a contact section AND tell me what font I'm using" = one code + one question).
- A text edit that should appear on the page is "code", never "copy".
- Preserve the user's intent — never invent extra tasks they didn't ask for."""

_llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
).with_structured_output(OrchestratorOutput)


def run_orchestrator(user_message: str) -> GlobalState:
    result: OrchestratorOutput = _llm.invoke(
        [{"role": "system", "content": _prompt},
         {"role": "user", "content": user_message}]
    )
    return GlobalState(
        intent=result.intent,
        sub_questions=result.sub_questions,
        status=["pending"] * len(result.sub_questions),
    )
