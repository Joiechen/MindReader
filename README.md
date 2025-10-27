# MindReader – TQC Report Intelligence Prototype

This repository contains a reference implementation for analysing existing TQC 大脑测评 reports with
a hybrid engine that blends configurable规则 and a ChatGPT5-driven narrative generator. The goal is to
help consultants upload基础报告, automatically extract actionable insights, and continue the
discussion with clients through多轮对话.

## Key Capabilities

- **Report ingestion** – load structured TQC assessment data into a canonical schema ready for
  processing.
- **Rule evaluation** – apply adjustable阈值 and条件 logic defined in JSON files to surface
  strengths,风险, and recommended干预措施.
- **LLM augmentation** – craft prompt templates and invoke a ChatGPT5分析引擎 (mocked in this
  prototype) to produce empathetic narratives.
- **Conversation orchestration** – maintain对话会话 state so clients can continue to ask questions
  and receive consistent answers grounded in their report.
- **Web 演示前端** – 通过 FastAPI 提供的单页界面，支持在线载入示例报告、触发分析以及与顾问助手对话。

## Repository Layout

- `backend/` – Python prototype for ingestion, rule evaluation, LLM integration, and conversation
  workflow.
- `config/` – Example rule packs that encode institutional经验.
- `docs/` – Architecture overview and扩展建议.
- `examples/` – Sample report payloads for演示.

## Getting Started

1. Ensure Python 3.11+ is available并安装依赖：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. 启动交互式 API + 前端演示：
   ```bash
   uvicorn backend.app.api:app --reload
   ```
3. 浏览器访问 <http://localhost:8000>，即可载入示例报告、运行规则分析并体验多轮对话。
4. 若仅需命令行演示，可继续运行：
   ```bash
   python -m backend.app.main
   ```
   在终端查看规则结果、叙事输出和示例对话。

## Customising the Engine

- Update `config/rules/*.json` with your own rule definitions or convert them to a managed rule
  catalogue stored in a database.
- Modify `backend/app/config.py` to point to additional rule files and adjust prompt parameters such
  as温度 and token limits.
- Replace the `_simulate_response` method in `backend/app/engines/llm_engine.py` with real ChatGPT5
  API calls and add moderation/safety checks to align with合规要求.
- Expand `ConversationService` to integrate with消息队列, WebSocket adapters, or CRM systems to
  deliver持续的客户支持.

## Additional Resources

- [System design overview](docs/tqc_system_design.md) – details on the ingestion pipeline, rule
  engine, LLM integration, and conversation architecture.

## Next Steps

- Build UI components that allow consultants to upload reports and monitor分析进度.
- Introduce长期趋势 tracking by aggregating multiple assessments per participant.
- Implement细粒度权限 control and审计日志 for data governance.
