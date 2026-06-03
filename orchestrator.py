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
   - "question": user is asking something about the page (no edits needed)

2. Decompose the message into sub-questions, each with a type:
   - "code": requires creating or editing files
   - "copy": requires generating text content (headlines, taglines, button labels)
   - "question": requires reading the page and answering

Rules:
- Keep sub-questions focused — one task each
- Preserve the original intent of the user, don't add extra tasks
- Order sub-questions logically (code changes before copy that depends on them)
- If the message is a single simple task, return just one sub-question"""

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
