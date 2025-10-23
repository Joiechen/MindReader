# MindReader Backend Prototype

This prototype demonstrates how existing TQC brain assessment reports can be ingested, analysed with
configurable rules, enhanced through a ChatGPT5-based engine, and exposed through a conversational
interface.

## Structure

- `app/config.py` – application configuration and default prompt definitions.
- `app/engines/rule_engine.py` – deterministic rule evaluation against structured report metrics.
- `app/engines/llm_engine.py` – ChatGPT5 prompt construction and mocked narrative generation.
- `app/services/report_service.py` – orchestration for loading reports and returning analysis
  artefacts.
- `app/services/conversation_service.py` – multi-turn chat workflow using existing analysis results.
- `app/schemas/` – dataclasses describing report inputs and analysis outputs.
- `examples/sample_report.json` – example TQC report payload.
- `config/rules/default_rules.json` – baseline rule definitions.

## Running the Demo

```bash
python -m backend.app.main
```

The demo will:

1. Load the sample report payload.
2. Evaluate rules and produce a mocked ChatGPT5 narrative.
3. Start a conversation session and respond to an example follow-up question.

## Extending the Prototype

- Replace `ChatGPT5Engine._simulate_response` with a real API integration.
- Add additional rule packs by dropping new JSON/YAML files into `config/rules` and referencing them
  in `AppConfig`.
- Implement new report parsers that transform PDFs or spreadsheets into the canonical
  `TqcReport` schema before invoking `ReportService`.
- Connect `ConversationService` to a persistent store (Redis, database) and expose WebSocket or
  HTTP endpoints for production chat experiences.
