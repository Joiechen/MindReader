"""Data structures representing TQC report inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class Participant:
    """Basic demographic information for a participant."""

    name: str
    age: int
    gender: str | None = None
    occupation: str | None = None


@dataclass
class TqcReport:
    """Canonical representation of an uploaded TQC brain assessment report."""

    report_id: str
    participant: Participant
    assessment_date: date
    assessment_type: str
    scores: Dict[str, float] = field(default_factory=dict)
    derived_metrics: Dict[str, float] = field(default_factory=dict)
    norm_reference: Dict[str, Any] = field(default_factory=dict)
    source_metadata: Dict[str, Any] = field(default_factory=dict)

    def get_metric(self, path: str) -> Optional[float]:
        """Retrieve a metric using dotted path notation (e.g., ``scores.attention``)."""

        parts = path.split(".")
        value: Any = self
        for part in parts:
            if isinstance(value, TqcReport) and hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        if isinstance(value, (int, float)):
            return float(value)
        return None
