"""Application configuration models for the TQC analysis platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class RuleConfig:
    """Represents a single rule definition loaded from configuration files."""

    id: str
    description: str
    targets: List[str]
    thresholds: List[Dict[str, float]] | None = None
    conditions: Dict[str, float] | None = None
    recommendation: str | None = None


@dataclass
class AppConfig:
    """Top-level settings used by the analysis engine."""

    rule_files: List[Path] = field(default_factory=list)
    prompt_templates: Dict[str, str] = field(default_factory=dict)
    llm_model: str = "chatgpt5-latest"
    llm_temperature: float = 0.4
    llm_max_tokens: int = 900


DEFAULT_PROMPTS: Dict[str, str] = {
    "baseline_summary": (
        "You are an expert TQC cognitive consultant. Summarise the participant's strengths, "
        "growth areas, and urgent risks using the provided metrics and rule outcomes. Keep the tone "
        "supportive, cite specific score values, and avoid medical claims."
    )
}


def load_default_config() -> AppConfig:
    """Create an ``AppConfig`` with repository defaults."""

    root = Path(__file__).resolve().parents[2]
    rule_path = root / "config" / "rules" / "default_rules.json"
    return AppConfig(rule_files=[rule_path], prompt_templates=DEFAULT_PROMPTS)
