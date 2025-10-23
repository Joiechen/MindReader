"""Command-line entry point demonstrating report analysis."""

from __future__ import annotations

from pathlib import Path

from .config import load_default_config
from .services.report_service import ReportService
from .services.conversation_service import ConversationService


def run_demo() -> None:
    config = load_default_config()
    service = ReportService(config)
    report_path = Path(__file__).resolve().parents[2] / "examples" / "sample_report.json"
    report = service.load_report(report_path)
    analysis = service.analyse(report)

    print("=== Rule Outcomes ===")
    for outcome in analysis.rule_outcomes:
        print(f"{outcome.rule_id}: {outcome.status} -> {outcome.recommendation}")

    if analysis.narrative:
        print("\n=== Narrative ===")
        print(analysis.narrative.response)

    conversation = ConversationService(config)
    session = conversation.start_session("demo-session", report, analysis)
    print("\n=== Conversation Intro ===")
    print(session.history[-1].content)

    answer = conversation.ask("demo-session", "我想了解注意力指标意味着什么？")
    print("\n=== Conversation Response ===")
    print(answer)


if __name__ == "__main__":
    run_demo()
