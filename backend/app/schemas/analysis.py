"""Data structures for analysis outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuleOutcome:
    """Result of applying a single rule to a report."""

    rule_id: str
    status: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendation: str | None = None


@dataclass
class NarrativeInsight:
    """Narrative response produced by the ChatGPT5 engine."""

    prompt_version: str
    response: str
    citations: List[str] = field(default_factory=list)
    safety_review: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Aggregate analysis artefact for a report."""

    report_id: str
    rule_outcomes: List[RuleOutcome]
    narrative: Optional[NarrativeInsight] = None

    def summary(self) -> Dict[str, Any]:
        """Return a condensed representation suitable for APIs."""

        return {
            "report_id": self.report_id,
            "rule_outcomes": [
                {
                    "rule_id": outcome.rule_id,
                    "status": outcome.status,
                    "recommendation": outcome.recommendation,
                }
                for outcome in self.rule_outcomes
            ],
            "has_narrative": self.narrative is not None,
        }
