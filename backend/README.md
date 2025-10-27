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

## Running the Demos

### Web 界面 + API

```bash
python -m backend.app.api
```

服务器会在 <http://localhost:8000> 启动，随后即可：

1. 载入仓库附带的示例报告或粘贴自定义 JSON。
2. 点击“运行分析”查看规则命中和 ChatGPT5 叙事摘要。
3. 在对话区域继续向顾问助手提问。

### 命令行演示

```bash
python -m backend.app.main
```

命令行模式会：

1. 加载示例报告。
2. 输出规则状态与模拟叙事。
3. 启动一次会话并打印示例问答。

## Extending the Prototype

- Replace `ChatGPT5Engine._simulate_response` with a real API integration.
- Add additional rule packs by dropping new JSON/YAML files into `config/rules` and referencing them
  in `AppConfig`.
- Implement new report parsers that transform PDFs or spreadsheets into the canonical
  `TqcReport` schema before invoking `ReportService`.
- Connect `ConversationService` to a persistent store (Redis, database) and expose WebSocket or
  HTTP endpoints for production chat experiences.
