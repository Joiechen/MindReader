"""LLM integration primitives for ChatGPT5."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List

from ..config import AppConfig
from ..schemas.analysis import NarrativeInsight, RuleOutcome
from ..schemas.report import TqcReport


@dataclass
class LlmRequest:
    """Payload sent to ChatGPT5."""

    model: str
    messages: List[Dict[str, str]]
    temperature: float
    max_tokens: int

    def to_json(self) -> str:
        return json.dumps(
            {
                "model": self.model,
                "messages": self.messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            ensure_ascii=False,
        )


class ChatGPT5Engine:
    """Facade around the ChatGPT5 API (stubbed for offline design)."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def build_prompt(self, report: TqcReport, outcomes: List[RuleOutcome], prompt_key: str) -> List[Dict[str, str]]:
        """Construct a chat-completion style prompt."""

        template = self._config.prompt_templates[prompt_key]
        system_message = {
            "role": "system",
            "content": template,
        }
        facts = [f"- {outcome.rule_id}: {outcome.status}" for outcome in outcomes]
        user_message = {
            "role": "user",
            "content": (
                "Participant: {name}, Age: {age}, Assessment: {assessment}.\n"
                "Key metrics: {metrics}.\n"
                "Rule outcomes:\n{rules}\n"
                "Please deliver an integrated narrative."
            ).format(
                name=report.participant.name,
                age=report.participant.age,
                assessment=report.assessment_type,
                metrics=", ".join(f"{k}={v}" for k, v in report.scores.items()),
                rules="\n".join(facts),
            ),
        }
        return [system_message, user_message]

    def generate_narrative(
        self, report: TqcReport, outcomes: List[RuleOutcome], prompt_key: str = "baseline_summary"
    ) -> NarrativeInsight:
        """Produce a narrative response (mocked for local execution)."""

        messages = self.build_prompt(report, outcomes, prompt_key)
        request = LlmRequest(
            model=self._config.llm_model,
            messages=messages,
            temperature=self._config.llm_temperature,
            max_tokens=self._config.llm_max_tokens,
        )

        # NOTE: In production this would call the ChatGPT5 API.
        # For this repository we simulate a deterministic response for demonstration.
        mock_response = self._simulate_response(report, outcomes)
        return NarrativeInsight(
            prompt_version=prompt_key,
            response=mock_response,
            citations=[outcome.rule_id for outcome in outcomes],
            safety_review={"status": "not_reviewed"},
        )

    def _simulate_response(self, report: TqcReport, outcomes: List[RuleOutcome]) -> str:
        strengths = [k for k, v in report.scores.items() if v >= 85]
        development = [k for k, v in report.scores.items() if v < 85]
        flagged = [o for o in outcomes if o.status in {"flagged", "Needs Support", "High Risk"}]

        lines = [
            f"{report.participant.name} recently completed the {report.assessment_type} on {report.assessment_date}.",
        ]
        if strengths:
            lines.append("Strength areas: " + ", ".join(strengths) + ".")
        if development:
            lines.append("Development priorities: " + ", ".join(development) + ".")
        if flagged:
            lines.append(
                "Flagged insights: "
                + "; ".join(
                    f"{o.rule_id} ({o.status}) – {o.recommendation or 'review recommended'}" for o in flagged
                )
                + "."
            )
        lines.append("Encourage the participant to discuss next steps with their consultant.")
        return "\n".join(lines)
