from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import PROTOCOL_VERSION
from .io_utils import write_json


FENCED_BLOCK_RE = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)
SEVERITIES = {"blocking", "warning", "note"}


def create_llm_review_request(
    generated_segments: list[dict[str, Any]],
    source_locale: str,
    target_locale: str,
    deterministic_findings: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
    max_segments: int = 80,
) -> dict[str, Any]:
    selected_segments = generated_segments[:max_segments]
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": f"llm-review-{run_id or 'ad-hoc'}",
        "run_id": run_id,
        "task": "llm_translation_reflection",
        "source_locale": source_locale,
        "target_locale": target_locale,
        "instructions": [
            "Review the draft translations for meaning, fluency, terminology, locale fit, and placeholder safety.",
            "Return actionable segment-level issues only.",
            "Every issue must include segment_id, severity, category, message, and confidence.",
            "Use severity=blocking for issues that should stop delivery, warning for issues that need human review, and note for low-risk observations.",
            "Do not rewrite every segment. Include suggested_target only when it materially helps the reviewer.",
        ],
        "output_contract": {
            "format": "json",
            "shape": {"issues": ["segment_id", "severity", "category", "message", "confidence", "suggested_target?"]},
            "segment_id_policy": "must_reference_request_segments",
        },
        "deterministic_findings": deterministic_findings or [],
        "segments": [
            {
                "segment_id": segment.get("segment_id"),
                "source_path": segment.get("source_path"),
                "source": segment.get("source"),
                "target": segment.get("target"),
                "context": segment.get("context", {}),
                "constraints": segment.get("constraints", {}),
            }
            for segment in selected_segments
        ],
        "summary": {
            "segment_count": len(selected_segments),
            "total_generated_segment_count": len(generated_segments),
            "deterministic_finding_count": len(deterministic_findings or []),
            "truncated": len(selected_segments) < len(generated_segments),
        },
    }


def render_llm_review_prompt(request: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# LLM Translation Review Prompt",
            "",
            f"- Request ID: `{request.get('request_id')}`",
            f"- Source locale: `{request.get('source_locale')}`",
            f"- Target locale: `{request.get('target_locale')}`",
            "",
            "Review the draft translations and return only JSON.",
            "The JSON must be an object with an `issues` array. Each issue must be tied to a segment_id.",
            "",
            "## Review Request",
            "",
            "```json",
            json.dumps(request, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )


def import_llm_review_response(
    request: dict[str, Any],
    response_text: str,
    output_json: Path | None = None,
) -> dict[str, Any]:
    expected_ids = {str(segment.get("segment_id")) for segment in request.get("segments", []) if segment.get("segment_id")}
    parsed = _parse_review_response(response_text)
    issues: list[dict[str, Any]] = []
    validation_items: list[dict[str, Any]] = []
    for raw in parsed:
        if not isinstance(raw, dict):
            validation_items.append(_validation_item("invalid_issue", "blocking", "LLM review issue must be an object"))
            continue
        segment_id = str(raw.get("segment_id") or "")
        severity = str(raw.get("severity") or "warning")
        if segment_id not in expected_ids:
            validation_items.append(_validation_item("unknown_segment_id", "blocking", f"Review issue references unknown segment_id: {segment_id}"))
            continue
        if severity not in SEVERITIES:
            validation_items.append(_validation_item("invalid_severity", "warning", f"Review issue has invalid severity: {severity}", segment_id))
            severity = "warning"
        issue = {
            "segment_id": segment_id,
            "severity": severity,
            "category": str(raw.get("category") or "llm_review"),
            "message": str(raw.get("message") or raw.get("rationale") or ""),
            "confidence": str(raw.get("confidence") or "unknown"),
            "channel": "llm",
        }
        if raw.get("suggested_target") is not None:
            issue["suggested_target"] = str(raw.get("suggested_target"))
        issues.append(issue)

    blocking = sum(issue["severity"] == "blocking" for issue in issues) + sum(
        item["severity"] == "blocking" for item in validation_items
    )
    warnings = sum(issue["severity"] == "warning" for issue in issues) + sum(
        item["severity"] == "warning" for item in validation_items
    )
    result = {
        "protocol_version": PROTOCOL_VERSION,
        "evidence_channels": ["llm"],
        "request_id": request.get("request_id"),
        "status": "fail" if blocking else "pass_with_warnings" if warnings else "pass",
        "summary": {
            "issue_count": len(issues),
            "blocking_count": blocking,
            "warning_count": warnings,
            "note_count": sum(issue["severity"] == "note" for issue in issues),
        },
        "issues": issues,
        "validation_items": validation_items,
    }
    if output_json is not None:
        write_json(output_json, result)
    return result


def _parse_review_response(response_text: str) -> list[Any]:
    errors: list[str] = []
    for candidate in _response_candidates(response_text):
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
            continue
        if isinstance(value, dict):
            issues = value.get("issues")
            if isinstance(issues, list):
                return issues
            errors.append("JSON object does not contain an issues array")
            continue
        if isinstance(value, list):
            return value
        errors.append("Review response must be a JSON object or array")
    detail = f": {'; '.join(errors[:3])}" if errors else ""
    raise ValueError(f"Could not parse LLM review response{detail}")


def _response_candidates(response_text: str) -> list[str]:
    candidates = [match.group(1).strip() for match in FENCED_BLOCK_RE.finditer(response_text)]
    stripped = response_text.lstrip("\ufeff").strip()
    if stripped:
        candidates.append(stripped)
    return candidates


def _validation_item(category: str, severity: str, message: str, segment_id: str | None = None) -> dict[str, Any]:
    item = {
        "channel": "runtime",
        "category": category,
        "severity": severity,
        "message": message,
        "checked_by": "runtime",
        "coverage": "complete",
        "confidence": "deterministic",
    }
    if segment_id:
        item["segment_id"] = segment_id
    return item
