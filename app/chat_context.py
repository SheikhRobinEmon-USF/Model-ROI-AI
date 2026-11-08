"""Prompt history budgets for the local studio."""
from typing import NamedTuple
import os


class ContextBudget(NamedTuple):
    turns: int
    characters: int
    question_characters: int
    tokens: int


def chat_budget():
    mode = os.environ.get("MODELROI_CHAT_CONTEXT", "standard").strip().lower()
    if mode == "extended":
        return ContextBudget(12, 8000, 2000, 8192)
    if mode == "standard":
        return ContextBudget(6, 3200, 800, 4096)
    raise ValueError("MODELROI_CHAT_CONTEXT must be standard or extended.")
