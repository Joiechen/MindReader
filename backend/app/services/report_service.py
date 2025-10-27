"""High-level orchestration for processing TQC reports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ..config import AppConfig, load_default_config
from ..engines.llm_engine import ChatGPT5Engine
from ..engines.rule_engine import RuleEngine
from ..schemas.analysis import AnalysisResult
from ..schemas.report import Participant, TqcReport


class ReportService:
    """Coordinate rule evaluation and LLM synthesis for a report."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or load_default_config()
        self._rule_engine = RuleEngine(self._config)
        self._llm_engine = ChatGPT5Engine(self._config)
        self._rule_engine.load_rules()

    def load_report(self, path: Path) -> TqcReport:
        """Load a report from JSON file."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        return self.parse_report(payload)

    def parse_report(self, payload: Dict[str, Any]) -> TqcReport:
        """Create a ``TqcReport`` instance from a dictionary payload."""

        if "participant" not in payload:
            raise ValueError("report payload must include participant information")
        if "report_id" not in payload:
            raise ValueError("report payload must include report_id")
        if "assessment_date" not in payload:
            raise ValueError("report payload must include assessment_date")
        if "assessment_type" not in payload:
            raise ValueError("report payload must include assessment_type")

        try:
            participant = Participant(**payload["participant"])
        except TypeError as exc:
            raise ValueError("participant information is incomplete") from exc
        try:
            assessment_date = datetime.fromisoformat(payload["assessment_date"]).date()
        except ValueError as exc:  # pragma: no cover - defensive parsing guard
            raise ValueError("assessment_date must be ISO formatted (YYYY-MM-DD)") from exc
        return TqcReport(
            report_id=payload["report_id"],
            participant=participant,
            assessment_date=assessment_date,
            assessment_type=payload["assessment_type"],
            scores=payload.get("scores", {}),
            derived_metrics=payload.get("derived_metrics", {}),
            norm_reference=payload.get("norm_reference", {}),
            source_metadata=payload.get("source_metadata", {}),
        )

    def analyse(self, report: TqcReport, with_narrative: bool = True) -> AnalysisResult:
        """Apply rules and optionally produce an LLM narrative."""

        rule_outcomes = self._rule_engine.evaluate(report)
        narrative = None
        if with_narrative:
            narrative = self._llm_engine.generate_narrative(report, rule_outcomes)
        return AnalysisResult(report_id=report.report_id, rule_outcomes=rule_outcomes, narrative=narrative)

    def export(self, analysis: AnalysisResult) -> Dict[str, Any]:
        """Convert the analysis result into a serialisable dictionary."""

        data: Dict[str, Any] = {
            "report_id": analysis.report_id,
            "rule_outcomes": [
                {
                    "rule_id": outcome.rule_id,
                    "status": outcome.status,
                    "evidence": outcome.evidence,
                    "recommendation": outcome.recommendation,
                }
                for outcome in analysis.rule_outcomes
            ],
        }
        if analysis.narrative:
            data["narrative"] = {
                "prompt_version": analysis.narrative.prompt_version,
                "response": analysis.narrative.response,
                "citations": analysis.narrative.citations,
                "safety_review": analysis.narrative.safety_review,
            }
        return data
