# TQC Brain Assessment Analysis Platform Design

## Overview
This document describes a modular analysis platform that can ingest existing TQC brain assessment
reports, apply configurable rule-driven evaluations, augment the insights with a ChatGPT5-powered
large-language-model (LLM) analysis engine, and surface the findings through an interactive,
multi-turn conversational experience for end users.

The design emphasises:

* **Flexible ingestion** of diverse report formats and templates used across TQC assessments.
* **Configurable rule engines** that encode domain knowledge and institutional standards.
* **LLM-assisted reasoning** that complements deterministic scoring with narrative synthesis,
  personalised recommendations, and contextual comparisons.
* **Conversation orchestration** so clients can explore clarifications, ask follow-up questions,
  and request deeper insights in natural language.
* **Governance and auditability** with transparent rule definitions, prompt templates, and
  reproducible output artefacts.

## High-Level Architecture

```
+----------------+        +----------------+        +----------------+        +-------------------+
| Report Sources | -----> | Ingestion &    | -----> | Analysis Core  | -----> | Experience Layer  |
|  (PDF, Excel,  |        | Normalisation  |        |                |        | (Web, Mobile,     |
|   JSON, etc.)  |        | Pipelines      |        |                |        |  Chat widgets)    |
+----------------+        +----------------+        +----------------+        +-------------------+
                                      |                     |                         |
                                      |                     |                         |
                                      v                     v                         v
                             +----------------+   +---------------------+     +-------------------+
                             | Rule Engine    |   | ChatGPT5 LLM Engine |     | Conversation Hub  |
                             +----------------+   +---------------------+     +-------------------+
```

### Key Components

1. **Ingestion Layer**
   * Accepts uploads of structured files (JSON, CSV), semi-structured documents (Excel), or
     unstructured PDFs.
   * Uses document parsers and data normalisers to map diverse inputs into a canonical
     `TqcReport` schema. Each parser declares required metadata (e.g., participant demographics,
     raw scores, normative references).
   * Implements validation rules to guarantee completeness (missing scores, unsupported test
     versions) before analysis proceeds.

2. **Analysis Core**
   * Orchestrates deterministic rule evaluations and probabilistic LLM generation.
   * Maintains versioned rule sets stored as JSON/YAML so specialists can tune scoring ranges,
     classification labels, and intervention strategies without redeploying code.
   * Provides prompt templates that blend structured findings (scores, deltas) with narrative
     framing to elicit consistent LLM outputs.
   * Persists the full analysis record, including intermediate rule results and the prompt/response
     pair exchanged with ChatGPT5, enabling audits.

3. **Conversation Hub**
   * Stores dialogue state per client session, referencing the underlying analysis artefacts.
   * Routes user questions either to retrieval-augmented responses (leveraging stored rule results
     and report metrics) or to follow-up LLM calls with guardrails.
   * Supports multi-turn context: user prompts are appended to the session transcript, trimmed with
     token windows to fit LLM limits, and augmented with citations of relevant report sections.

4. **Experience Layer**
   * Offers APIs/SDKs for integration with portals or mini-programs.
   * Provides event streams (webhooks or message queues) so downstream systems can react to new
     analyses, e.g., notifying consultants when high-risk findings arise.

## Data Model

### Canonical Report (`TqcReport`)

| Field                     | Type        | Description                                                       |
|---------------------------|-------------|-------------------------------------------------------------------|
| `report_id`               | string      | Unique identifier for the uploaded report.                        |
| `participant`             | object      | Contains demographics: name, age, gender, education, etc.         |
| `assessment_date`         | date        | Test administration date.                                         |
| `assessment_type`         | string      | Specific TQC test battery or version.                             |
| `scores`                  | object      | Key-value pairs of metric names (e.g., attention, memory) to raw scores or percentiles. |
| `derived_metrics`         | object      | Computed indexes (e.g., cognitive balance score).                  |
| `norm_reference`          | object      | Cohort statistics used for comparison.                             |
| `source_metadata`         | object      | Parser-specific metadata (file source, upload user, etc.).         |
| `attachments`             | list        | Links to original files or supplementary documents.               |

### Rule Result (`RuleEvaluation`)

| Field           | Type   | Description                                                 |
|-----------------|--------|-------------------------------------------------------------|
| `rule_id`       | string | Identifier referencing the configuration file.             |
| `status`        | enum   | `passed`, `flagged`, or `not_applicable`.                   |
| `evidence`      | object | Data points supporting the decision.                       |
| `recommendation`| text   | Human-readable guidance or next steps.                      |

### LLM Narrative (`NarrativeInsight`)

| Field            | Type   | Description                                                 |
|------------------|--------|-------------------------------------------------------------|
| `prompt_version` | string | Prompt template identifier.                                |
| `response`       | text   | ChatGPT5 generated narrative.                              |
| `citations`      | list   | References to rule outcomes or report metrics.             |
| `safety_review`  | object | Scores/confidence from automated moderation filters.       |

## Rule Configuration Strategy

* Store rule files as JSON/YAML with the following structure:
  ```json
  {
    "id": "cognitive_balance_band",
    "description": "Categorise cognitive balance index into risk tiers.",
    "targets": ["derived_metrics.cognitive_balance"],
    "thresholds": [
      {"label": "Optimal", "min": 80, "max": 100, "recommendation": "Maintain current habits."},
      {"label": "Watch", "min": 65, "max": 79, "recommendation": "Introduce stress management exercises."},
      {"label": "High Risk", "min": 0, "max": 64, "recommendation": "Schedule targeted cognitive coaching."}
    ]
  }
  ```
* Rules can reference derived calculations (e.g., z-score comparisons, year-over-year changes).
* Allow chaining: results from one rule can feed into conditions of another through a
  lightweight dependency graph.
* Provide an interpretation DSL for complex logic, e.g., boolean expressions across multiple
  metrics or pattern detection in longitudinal data.

## ChatGPT5 Integration Model

1. **Prompt Composition**
   * Combine deterministic facts: participant profile, top findings, flagged risks, goals.
   * Embed rule outputs as structured bullet points, instructing the LLM to expand into empathetic
     language while retaining factual grounding.
   * Include guardrails (do not override medical advice, cite data points, highlight uncertainties).

2. **Response Post-Processing**
   * Run automated moderation and redaction filters to ensure compliance.
   * Extract structured highlights (e.g., “Key Strengths”, “Areas for Improvement”) for downstream
     display.
   * Store conversation metadata for reproducibility.

3. **Model Management**
   * Wrap ChatGPT5 API via a service that supports:
     * Model/version selection.
     * Temperature, max token, and top-p overrides per use case.
     * Retry logic with exponential backoff and fallback prompts.
     * Cost tracking and rate limiting per tenant.

## Conversation Workflow

1. Client submits a query referencing their completed analysis.
2. The Conversation Service retrieves the stored transcript and relevant artefacts
   (rule results, LLM narratives, raw metrics).
3. The Orchestrator decides whether the response can be composed purely from existing data
   (using templated messages and retrieval) or requires a new LLM call.
4. When invoking the LLM, the system supplies:
   * Conversation history trimmed to fit the token budget.
   * Highlighted metrics relevant to the user’s query.
   * Clarifying instructions (e.g., remain consistent with previously delivered results).
5. The response is logged, appended to the transcript, and optionally summarised for analytics.

## Deployment Considerations

* **Microservice separation**: ingestion, analysis, and conversation services can scale independently.
* **Data privacy**: enforce encryption at rest, role-based access control, and consent tracking for
  sensitive cognitive assessment data.
* **Observability**: integrate structured logging, distributed tracing, and rule/LLM output monitors.
* **Extensibility**: plugin architecture for new report types, rule packs, and prompt templates.

## Roadmap Extensions

* **Longitudinal insights**: compare multiple assessments per client to detect trends.
* **Adaptive questioning**: use conversational feedback to schedule follow-up assessments.
* **Consultant co-pilot**: allow human experts to annotate results which feed back into prompt
  fine-tuning and rule updates.
* **A/B experimentation**: evaluate different prompt strategies or rule parameter sets for outcome
  quality.

## Summary

The proposed platform blends deterministic expertise encoded in configurable rules with the
flexibility of a ChatGPT5 LLM to deliver rich, conversational insights on top of TQC brain
assessment data. By separating ingestion, analysis, and interaction concerns, the system remains
adaptable to evolving assessment methodologies and client needs while preserving governance and
auditability required for sensitive cognitive evaluations.
