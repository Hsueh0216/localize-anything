from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import PROTOCOL_VERSION
from .io_utils import read_jsonl, write_jsonl
from .json_adapter import extract_placeholders


DEFAULT_PROVIDER = "codex-local"
DEFAULT_QUALITY_CLAIM = "local_chinese_draft_for_e2e"

EXACT_TRANSLATIONS = {
    "Sample App": "\u793a\u4f8b\u5e94\u7528",
    "Welcome, %1$s!": "\u6b22\u8fce\uff0c%1$s\uff01",
    "Welcome, %@!": "\u6b22\u8fce\uff0c%@\uff01",
    "You have %d coins.": "\u4f60\u6709 %d \u679a\u786c\u5e01\u3002",
    "Battery at 100%": "\u7535\u91cf 100%",
    "Home": "\u9996\u9875",
    "Settings": "\u8bbe\u7f6e",
    "%d message": "%d \u6761\u6d88\u606f",
    "%d messages": "%d \u6761\u6d88\u606f",
}

TERM_TRANSLATIONS = {
    "Add": "\u6dfb\u52a0",
    "All": "\u5168\u90e8",
    "Cancel": "\u53d6\u6d88",
    "Clear": "\u6e05\u9664",
    "Close": "\u5173\u95ed",
    "Continue": "\u7ee7\u7eed",
    "Delete": "\u5220\u9664",
    "Download": "\u4e0b\u8f7d",
    "Edit": "\u7f16\u8f91",
    "Episode": "\u5355\u96c6",
    "Episodes": "\u5355\u96c6",
    "Error": "\u9519\u8bef",
    "Feed": "\u8ba2\u9605\u6e90",
    "Feeds": "\u8ba2\u9605\u6e90",
    "Home": "\u9996\u9875",
    "Import": "\u5bfc\u5165",
    "Inbox": "\u6536\u4ef6\u7bb1",
    "Next": "\u4e0b\u4e00\u6b65",
    "OK": "\u786e\u5b9a",
    "Open": "\u6253\u5f00",
    "Pause": "\u6682\u505c",
    "Play": "\u64ad\u653e",
    "Podcast": "\u64ad\u5ba2",
    "Podcasts": "\u64ad\u5ba2",
    "Preferences": "\u504f\u597d\u8bbe\u7f6e",
    "Queue": "\u961f\u5217",
    "Remove": "\u79fb\u9664",
    "Save": "\u4fdd\u5b58",
    "Search": "\u641c\u7d22",
    "Settings": "\u8bbe\u7f6e",
    "Skip": "\u8df3\u8fc7",
    "Subscribe": "\u8ba2\u9605",
    "Update": "\u66f4\u65b0",
    "Warning": "\u8b66\u544a",
}

ASCII_LETTER_RE = re.compile(r"[A-Za-z]")
RESOURCE_REFERENCE_RE = re.compile(r"^@(?:[A-Za-z_][\w.]*:)?[A-Za-z_][\w.]*/[A-Za-z_][\w.]*$")


def draft_chinese_text(source: str, placeholders: list[str] | None = None) -> str:
    """Create a conservative Chinese draft while preserving source tokens.

    This is a local E2E testing helper, not a publication-quality translator.
    Unknown strings keep their source text with a Chinese draft prefix so Android
    placeholder and resource QA can still validate the full delivery path.
    """

    placeholders = placeholders or []
    if source == "":
        return ""
    if RESOURCE_REFERENCE_RE.match(source):
        return source
    if source in EXACT_TRANSLATIONS:
        return _ensure_placeholders(EXACT_TRANSLATIONS[source], placeholders)

    translated = source
    for english, chinese in sorted(TERM_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(rf"\b{re.escape(english)}\b", chinese, translated, flags=re.IGNORECASE)

    if translated == source and ASCII_LETTER_RE.search(source):
        translated = f"\u4e2d\u6587\u8349\u7a3f\uff1a{source}"
    elif translated == source:
        translated = f"\u8349\u7a3f\uff1a{source}"

    return _ensure_placeholders(translated, placeholders)


def generate_chinese_draft_segments(
    segments: list[dict[str, Any]],
    target_locale: str = "zh-CN",
    provider: str = DEFAULT_PROVIDER,
    quality_claim: str = DEFAULT_QUALITY_CLAIM,
) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for segment in segments:
        source = str(segment.get("source", ""))
        placeholders = [str(item) for item in segment.get("constraints", {}).get("placeholders", [])]
        record = dict(segment)
        record["target_locale"] = target_locale
        record["target"] = draft_chinese_text(source, placeholders)
        record["status"] = "generated"
        record["generation"] = {
            "provider": provider,
            "quality_claim": quality_claim,
            "purpose": "android_app_e2e_test",
            "method": "local_dictionary_and_source_preserving_draft",
        }
        generated.append(record)
    return generated


def generate_chinese_draft_file(
    segments_path: Path,
    generated_output: Path,
    target_locale: str = "zh-CN",
    provider: str = DEFAULT_PROVIDER,
    quality_claim: str = DEFAULT_QUALITY_CLAIM,
) -> dict[str, Any]:
    segments = read_jsonl(segments_path)
    generated = generate_chinese_draft_segments(segments, target_locale, provider, quality_claim)
    write_jsonl(generated_output, generated)
    placeholder_mismatches = [
        segment["segment_id"]
        for segment in generated
        if sorted(str(item) for item in segment.get("constraints", {}).get("placeholders", []))
        != extract_placeholders(str(segment.get("target", "")))
    ]
    status = "fail" if placeholder_mismatches else "pass"
    return {
        "protocol_version": PROTOCOL_VERSION,
        "evidence_channels": ["runtime"],
        "status": status,
        "input_segments": segments_path.as_posix(),
        "generated_output": generated_output.as_posix(),
        "target_locale": target_locale,
        "provider": provider,
        "quality_claim": quality_claim,
        "summary": {
            "segment_count": len(segments),
            "generated_segment_count": len(generated),
            "placeholder_mismatch_count": len(placeholder_mismatches),
        },
        "items": [
            {
                "category": "placeholder_parity",
                "severity": "blocking",
                "message": f"Generated draft target lost placeholders for {segment_id}",
                "segment_id": segment_id,
            }
            for segment_id in placeholder_mismatches
        ],
    }


def _ensure_placeholders(target: str, placeholders: list[str]) -> str:
    missing = [placeholder for placeholder in placeholders if placeholder not in extract_placeholders(target)]
    if not missing:
        return target
    suffix = " ".join(missing)
    return f"{target} {suffix}".strip()
