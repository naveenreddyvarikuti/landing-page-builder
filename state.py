from typing import Literal, Optional
from pydantic import BaseModel, Field


class SubQuestion(BaseModel):
    question: str
    type: Literal["code", "copy", "question"]


class GlobalState(BaseModel):
    intent: Literal["create", "edit", "question"]
    sub_questions: list[SubQuestion]
    current_index: int = 0
    status: list[Literal["pending", "in_progress", "done", "failed"]] = Field(default_factory=list)
    attempt: int = 1
    max_attempts: int = 3
    reviewer_feedback: Optional[str] = None
    change_log: list[dict] = Field(default_factory=list)
    conversation_history: list[dict] = Field(default_factory=list)

    def current_sub_question(self) -> SubQuestion:
        return self.sub_questions[self.current_index]

    def is_done(self) -> bool:
        return self.current_index >= len(self.sub_questions)

    def advance(self) -> None:
        self.status[self.current_index] = "done"
        self.current_index += 1
        self.attempt = 1
        self.reviewer_feedback = None
