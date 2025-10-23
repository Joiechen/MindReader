"""Rule evaluation engine for TQC reports."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from ..config import AppConfig, RuleConfig
from ..schemas.analysis import RuleOutcome
from ..schemas.report import TqcReport


class RuleEngine:
    """Evaluate configured rules against a ``TqcReport`` instance."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._rules: List[RuleConfig] = []

    def load_rules(self) -> None:
        """Load rule definitions from configuration files."""

        self._rules.clear()
        for path in self._config.rule_files:
            self._rules.extend(self._load_rule_file(path))

    def evaluate(self, report: TqcReport) -> List[RuleOutcome]:
        """Execute every rule against the provided report."""

        outcomes: List[RuleOutcome] = []
        for rule in self._rules:
            outcome = self._evaluate_rule(rule, report)
            outcomes.append(outcome)
        return outcomes

    def _evaluate_rule(self, rule: RuleConfig, report: TqcReport) -> RuleOutcome:
        evidence = {}
        status = "not_applicable"
        recommendation = rule.recommendation

        for target in rule.targets:
            metric = report.get_metric(target)
            evidence[target] = metric

            if metric is None:
                continue

            if rule.thresholds:
                status = self._evaluate_thresholds(metric, rule, evidence)
            elif rule.conditions:
                status = self._evaluate_conditions(metric, rule)
            else:
                status = "passed"

        return RuleOutcome(
            rule_id=rule.id,
            status=status,
            evidence=evidence,
            recommendation=recommendation,
        )

    def _evaluate_thresholds(self, metric: float, rule: RuleConfig, evidence: dict) -> str:
        for threshold in rule.thresholds or []:
            min_val = threshold.get("min", float("-inf"))
            max_val = threshold.get("max", float("inf"))
            if min_val <= metric <= max_val:
                evidence["matched_threshold"] = threshold
                return threshold.get("label", "passed")
        return "out_of_range"

    def _evaluate_conditions(self, metric: float, rule: RuleConfig) -> str:
        conditions = rule.conditions or {}
        if "gt" in conditions and not metric > conditions["gt"]:
            return "passed"
        if "lt" in conditions and metric < conditions["lt"]:
            return "flagged"
        if "eq" in conditions and metric == conditions["eq"]:
            return "flagged"
        return "passed"

    def _load_rule_file(self, path: Path) -> Iterable[RuleConfig]:
        data = json.loads(path.read_text(encoding="utf-8"))
        for rule_dict in data:
            yield RuleConfig(**rule_dict)

    def export_rules(self) -> List[dict]:
        """Return the loaded rules for inspection or API responses."""

        return [asdict(rule) for rule in self._rules]
