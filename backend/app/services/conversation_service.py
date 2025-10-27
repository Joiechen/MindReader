"""Conversation management for multi-turn client dialogues."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List

from ..config import AppConfig
from ..engines.llm_engine import ChatGPT5Engine
from ..schemas.analysis import AnalysisResult, RuleOutcome
from ..schemas.report import TqcReport


@dataclass
class Message:
    """Single conversational message."""

    role: str
    content: str


@dataclass
class ConversationSession:
    """Stateful conversation tied to a specific report analysis."""

    session_id: str
    report: TqcReport
    analysis: AnalysisResult
    history: Deque[Message] = field(default_factory=lambda: deque(maxlen=15))

    def add(self, role: str, content: str) -> None:
        self.history.append(Message(role=role, content=content))

    def serialize(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            "session_id": self.session_id,
            "history": [message.__dict__ for message in self.history],
        }


class ConversationService:
    """Handle multi-turn chat leveraging analysis artefacts."""

    def __init__(self, config: AppConfig, llm_engine: ChatGPT5Engine | None = None) -> None:
        self._config = config
        self._llm_engine = llm_engine or ChatGPT5Engine(config)
        self._sessions: Dict[str, ConversationSession] = {}

    def start_session(self, session_id: str, report: TqcReport, analysis: AnalysisResult) -> ConversationSession:
        session = ConversationSession(session_id=session_id, report=report, analysis=analysis)
        self._sessions[session_id] = session
        intro = (
            "您好！我已经读取了您的TQC测评结果，如果需要了解某项指标或建议，请直接提问。"
        )
        session.add("assistant", intro)
        return session

    def ask(self, session_id: str, question: str) -> str:
        session = self._sessions[session_id]
        session.add("user", question)

        synthesized = self._compose_response(question, session.analysis.rule_outcomes)
        session.add("assistant", synthesized)
        return synthesized

    def escalate_to_llm(self, session_id: str) -> str:
        session = self._sessions[session_id]
        narrative = self._llm_engine.generate_narrative(
            report=session.report,
            outcomes=session.analysis.rule_outcomes,
        )
        session.add("assistant", narrative.response)
        return narrative.response

    def _compose_response(self, question: str, outcomes: List[RuleOutcome]) -> str:
        """Create a lightweight retrieval-based response without new LLM calls."""

        highlights = []
        for outcome in outcomes:
            label = outcome.status
            if outcome.recommendation:
                label += f" — {outcome.recommendation}"
            highlights.append(f"{outcome.rule_id}: {label}")

        response = (
            "您提到的问题是：“{question}”。以下是报告中的要点，供您参考：\n"
            "{points}\n"
            "如需更详细的解释，我可以为您生成更完整的说明。"
        ).format(question=question, points="\n".join(f"- {item}" for item in highlights))
        return response
