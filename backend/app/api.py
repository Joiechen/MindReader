"""FastAPI application exposing analysis and conversation endpoints with a demo frontend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import load_default_config
from .services.conversation_service import ConversationService
from .services.report_service import ReportService


class AnalyzeRequest(BaseModel):
    """Request payload for running report analysis."""

    report: Dict[str, Any]
    with_narrative: bool = True
    session_id: str | None = Field(default=None, description="Optional session identifier")


class AnalyzeResponse(BaseModel):
    """Response for a completed analysis request."""

    session_id: str
    intro_message: str
    analysis: Dict[str, Any]


class AskRequest(BaseModel):
    """Payload for a follow-up conversation question."""

    question: str


class AskResponse(BaseModel):
    """Response returned for a conversation turn."""

    response: str


class SampleReportResponse(BaseModel):
    """Return structure for the bundled sample report."""

    report: Dict[str, Any]


config = load_default_config()
report_service = ReportService(config)
conversation_service = ConversationService(config)

app = FastAPI(title="MindReader API", description="TQC report analysis and conversation demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    """Simple readiness probe."""

    return {"status": "ok"}


@app.get("/api/sample-report", response_model=SampleReportResponse)
def get_sample_report() -> SampleReportResponse:
    """Return the repository's bundled sample report payload."""

    sample_path = Path(__file__).resolve().parents[2] / "examples" / "sample_report.json"
    try:
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard for missing file
        raise HTTPException(status_code=500, detail="Sample report not available") from exc
    return SampleReportResponse(report=payload)


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_report(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run analysis over an uploaded report and start a conversation session."""

    try:
        report = report_service.parse_report(request.report)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    analysis = report_service.analyse(report, with_narrative=request.with_narrative)
    session_id = request.session_id or str(uuid4())
    session = conversation_service.start_session(session_id, report, analysis)

    return AnalyzeResponse(
        session_id=session.session_id,
        intro_message=session.history[-1].content,
        analysis=report_service.export(analysis),
    )


@app.post("/api/conversations/{session_id}/ask", response_model=AskResponse)
def ask_question(session_id: str, request: AskRequest) -> AskResponse:
    """Answer a follow-up question within an existing conversation session."""

    try:
        response = conversation_service.ask(session_id, request.question)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown session id") from exc
    return AskResponse(response=response)


_frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
_static_dir = _frontend_dir / "static"

if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    """Serve the demo frontend."""

    index_path = _frontend_dir / "index.html"
    if not index_path.exists():  # pragma: no cover - runtime guard for missing asset
        raise HTTPException(status_code=404, detail="Frontend not built")
    return FileResponse(index_path)
