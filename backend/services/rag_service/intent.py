"""Bounded English routing hints; the answer model still interprets the question."""

import re
from typing import Literal

from pydantic import BaseModel


class QuestionPlan(BaseModel):
    intent: Literal["summary", "topic", "fact", "analysis", "comparison", "general", "mixed"]
    retrieval_query: str
    allow_general: bool = False
    uses_history: bool = False

    def context_limit(self, factual_limit: int) -> int:
        return factual_limit if self.intent == "fact" else min(20, max(factual_limit, 12))


def plan_question(
    question: str, history: list[dict[str, str]] | None = None, max_query_bytes: int = 12000
) -> QuestionPlan:
    """Use prior questions as retrieval context, never as factual source evidence."""
    history = history or []
    lower = question.lower()
    follow_up = bool(history) and bool(
        re.search(r"\b(those|these|that|their|they|it)\b|^\s*(what about|and\b)", lower)
        or lower.strip(" ?.") in {"why", "how", "why not"}
    )
    query = question
    if follow_up:
        query += "\nPrevious question for context: " + history[-1].get("question", "")[:2000]
    terms = query.lower()
    paper = bool(re.search(r"\b(paper|article|study|authors?|document|researchers?)\b", lower))
    explicit_general = bool(
        re.search(
            r"\b(in general|generally|general (?:background|knowledge|explanation))\b|beyond (?:this|the) paper",
            lower,
        )
    )
    fact = bool(
        re.search(
            r"\b(how many|number of|participants?|sample size|accuracy|percentage|dataset|title|authors?|methodology)\b",
            lower,
        )
    )
    definition = bool(re.search(r"^\s*(?:please\s+)?(what is|what are|define|explain)\b", lower))
    general = explicit_general or (
        definition
        and not paper
        and not fact
        and not follow_up
        and not re.search(r"\b(these|those|their|this finding|this result)\b", lower)
    )
    summary = bool(
        re.search(
            r"\b(summari[sz]e|summary|overview)\b|what (?:is|was) .*(?:paper|study|article) about",
            lower,
        )
    )
    topical_summary = bool(
        re.search(r"\b(gender|sex|women|men|regarding|focused on|focus on)\b", lower)
    )

    if general:
        intent = "mixed" if paper else "general"
    elif summary and not topical_summary:
        intent = "summary"
    elif re.search(r"\b(compare|comparison|differ|differences|versus|vs)\b|between .+ and ", lower):
        intent = "comparison"
    elif re.search(r"^\s*why\b|\b(reason|limitations?|explain|interpret|how did|how do)\b", lower):
        intent = "analysis"
    elif re.search(r"\b(about|discuss|say|gender|topic|regarding|findings)\b", lower):
        intent = "topic"
    else:
        intent = "fact"
    if intent in {"topic", "comparison", "analysis", "mixed"} and re.search(
        r"\b(gender|sex|men|women|male|female)\b", terms
    ):
        query += "\nRelated terms: gender sex men women male female boys girls."
    query = query.encode("utf-8")[:max_query_bytes].decode("utf-8", errors="ignore")
    return QuestionPlan(
        intent=intent, retrieval_query=query, allow_general=general, uses_history=follow_up
    )
