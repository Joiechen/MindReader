"""Lightweight HTTP server exposing analysis and conversation endpoints."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import urlparse
from uuid import uuid4

from .config import load_default_config
from .services.conversation_service import ConversationService
from .services.report_service import ReportService


_ROOT_DIR = Path(__file__).resolve().parents[2]
_FRONTEND_DIR = _ROOT_DIR / "frontend"


config = load_default_config()
report_service = ReportService(config)
conversation_service = ConversationService(config)


class MindReaderRequestHandler(SimpleHTTPRequestHandler):
    """Serve static assets and JSON API endpoints from a single handler."""

    server_version = "MindReader/0.1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(_FRONTEND_DIR), **kwargs)

    # Silence default logging noise to keep demo output concise.
    def log_message(self, format: str, *args: Any) -> None:  # noqa: D401 - inherited signature
        """Redirect default logging to stdout with a compact prefix."""

        message = "%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args)
        print(message, end="")

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload") from exc

    def _send_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _extract_session_path(self, path: str) -> Tuple[str, str] | None:
        parts = [segment for segment in path.split("/") if segment]
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "conversations" and parts[3] == "ask":
            # /api/conversations/<session_id>/ask
            return parts[2], parts[3]
        return None

    # ---------------------------------------------------------------------
    # HTTP verb implementations
    # ---------------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: D401 - inherited signature
        """Serve API responses or static assets."""

        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return

        if parsed.path == "/api/sample-report":
            sample_path = _ROOT_DIR / "examples" / "sample_report.json"
            try:
                payload = json.loads(sample_path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"detail": "Sample report not available"})
            else:
                self._send_json(HTTPStatus.OK, {"report": payload})
            return

        if parsed.path == "/":
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self) -> None:  # noqa: D401 - inherited signature
        """Dispatch POST requests to analysis or conversation handlers."""

        parsed = urlparse(self.path)

        if parsed.path == "/api/analyze":
            try:
                payload = self._read_json()
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
                return

            report_payload = payload.get("report")
            if not isinstance(report_payload, dict):
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": "Missing or invalid report"})
                return

            with_narrative = bool(payload.get("with_narrative", True))
            session_id = payload.get("session_id") or str(uuid4())

            try:
                report = report_service.parse_report(report_payload)
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
                return

            analysis = report_service.analyse(report, with_narrative=with_narrative)
            session = conversation_service.start_session(session_id, report, analysis)

            response_payload = {
                "session_id": session.session_id,
                "intro_message": session.history[-1].content,
                "analysis": report_service.export(analysis),
            }
            self._send_json(HTTPStatus.OK, response_payload)
            return

        session_match = self._extract_session_path(parsed.path)
        if session_match:
            session_id, _ = session_match
            try:
                payload = self._read_json()
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
                return

            question = payload.get("question")
            if not question or not isinstance(question, str):
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": "Missing question"})
                return

            try:
                response = conversation_service.ask(session_id, question)
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"detail": "Unknown session id"})
                return

            self._send_json(HTTPStatus.OK, {"response": response})
            return

        self.send_error(HTTPStatus.NOT_FOUND.value, "Unsupported endpoint")


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the threaded HTTP server."""

    if not _FRONTEND_DIR.exists():
        raise RuntimeError("Frontend assets are missing; run from the project root.")

    server = ThreadingHTTPServer((host, port), MindReaderRequestHandler)
    address = f"http://{host}:{port}"
    print(f"MindReader demo server running on {address}. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()


if __name__ == "__main__":  # pragma: no cover - manual execution guard
    run()
