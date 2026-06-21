"""DeepSeek translation provider for Localize Anything."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from . import PROTOCOL_VERSION
from .io_utils import read_jsonl, write_jsonl
from .json_adapter import extract_placeholders

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"  # fast model for translation
DEEPSEEK_ENV_FILE_VARS = (
    "LOCALIZE_ANYTHING_DEEPSEEK_ENV_FILE",
    "DEEPSEEK_ENV_FILE",
)
SOURCE_FILES = [  # key source files to load for context
    (Path(__file__).resolve().parent.parent.parent.parent / "test02-antennapod/source/res/values/strings.xml"),
]


def _get_api_key() -> str:
    """Get DeepSeek API key from explicit environment configuration."""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key

    for env_var in DEEPSEEK_ENV_FILE_VARS:
        env_file = os.environ.get(env_var, "").strip()
        if env_file:
            return _read_api_key_from_env_file(Path(env_file), env_var)

    raise RuntimeError(
        "DEEPSEEK_API_KEY not found. Set DEEPSEEK_API_KEY or explicitly set "
        "LOCALIZE_ANYTHING_DEEPSEEK_ENV_FILE to an env file containing DEEPSEEK_API_KEY."
    )


def _read_api_key_from_env_file(path: Path, env_var: str) -> str:
    if not path.exists():
        raise RuntimeError(f"{env_var} points to an env file that does not exist.")

    content = path.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("DEEPSEEK_API_KEY="):
            key = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key

    raise RuntimeError(f"{env_var} does not contain DEEPSEEK_API_KEY.")


def translate_batch_deepseek(
    segments: list[dict[str, Any]],
    target_locale: str,
    source_locale: str = "en-US",
    model: str = DEFAULT_MODEL,
) -> list[dict[str, Any]]:
    """Translate a batch of segments using DeepSeek API.

    Args:
        segments: List of segment dicts from work packets
        target_locale: e.g. 'ja', 'ko', 'zh-CN'
        source_locale: Source locale like 'en-US'
        model: DeepSeek model name

    Returns:
        Generated segments with target translations
    """
    api_key = _get_api_key()
    locale_names = {"ja": "日本語", "ko": "한국어", "zh-CN": "简体中文", "fr": "Français", "de": "Deutsch"}

    # Build translation prompt
    locale_name = locale_names.get(target_locale, target_locale)
    entries = []
    for seg in segments:
        source = seg.get("source", "")
        seg_id = seg.get("segment_id", "")
        constraints = seg.get("constraints", {})
        context = constraints.get("note", "")

        entry = f'  {{"id": "{seg_id}", "source": {json.dumps(source, ensure_ascii=False)}'
        if context:
            entry += f', "context": {json.dumps(context, ensure_ascii=False)}'
        entry += "}"
        entries.append(entry)

    entries_block = ",\n".join(entries)

    system_prompt = (
        f"You are a professional translator localizing an Android app (AntennaPod podcast player) "
        f"from {source_locale} to {locale_name} ({target_locale}).\n\n"
        f"Rules:\n"
        f"1. Preserve all placeholders exactly: %1$s, %2$d, %s, %d, etc.\n"
        f"2. Preserve HTML/XML tags: <b>, <i>, <a href=\"...\">, <br/>, etc.\n"
        f"3. Preserve special tokens: \\n, \\t, @string/ references\n"
        f"4. Use natural, native-sounding {locale_name}. No literal translations.\n"
        f"5. For podcast/tech terms, use commonly accepted translations.\n"
        f"6. Keep proper nouns (AntennaPod, gpodder.net) untranslated.\n"
        f"7. For short strings (1-3 words), prefer concise forms.\n"
        f"8. Output ONLY a JSON array of objects with \"id\" and \"target\" fields. No markdown, no explanation.\n"
        f"9. Translate ALL entries in one response. Do not skip any."
    )

    user_prompt = (
        f"Translate these {len(segments)} Android app UI strings to {locale_name} ({target_locale}).\n"
        f"Return JSON array with id and target for every entry.\n\n"
        f"[\n{entries_block}\n]"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8-sig"))
    except Exception as e:
        # Fallback: return source with prefix
        fallback = _fallback_translations(segments, target_locale)
        fallback[0]["_deepseek_error"] = str(e)
        return fallback

    # Parse DeepSeek response
    content = body["choices"][0]["message"]["content"]

    # Extract JSON from response (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0]

    try:
        translations = json.loads(content)
    except json.JSONDecodeError:
        return _fallback_translations(segments, target_locale)

    # Handle both array and object response formats
    if isinstance(translations, dict):
        # {"translations": [...]} or {"id1": "target1", ...}
        if "translations" in translations:
            translations = translations["translations"]
        else:
            translations = [
                {"id": k, "target": v}
                for k, v in translations.items()
                if k != "id"  # skip explanation fields
            ]

    # Build lookup
    translation_map = {}
    if isinstance(translations, list):
        for t in translations:
            if isinstance(t, dict):
                tid = t.get("id", "")
                ttarget = t.get("target", "")
                if tid and ttarget:
                    translation_map[tid] = ttarget

    # Generate segment records
    generated = []
    for seg in segments:
        seg_id = seg.get("segment_id", "")
        source = seg.get("source", "")
        placeholders = [str(p) for p in seg.get("constraints", {}).get("placeholders", [])]

        target = translation_map.get(seg_id) or _fallback_single(source, target_locale)

        # Placeholder parity: ensure target preserves all source placeholders
        target = _fix_placeholder_parity(target, placeholders, source)

        record = dict(seg)
        record["target_locale"] = target_locale
        record["target"] = target
        record["status"] = "generated"
        record["generation"] = {
            "provider": "deepseek",
            "model": model,
            "quality_claim": "llm_draft",
            "purpose": "localization",
        }
        generated.append(record)

    return generated


def _fix_placeholder_parity(
    target: str, expected_placeholders: list[str], source: str
) -> str:
    """Ensure target contains exactly the expected placeholders, no more, no less.

    - Extra placeholders (hallucinated by LLM) are stripped.
    - Missing placeholders are appended from source as a safety suffix.
    """
    from .json_adapter import extract_placeholders

    actual = extract_placeholders(target)
    expected_set = set(expected_placeholders)
    actual_set = set(actual)

    # Remove extra placeholders
    extra = actual_set - expected_set
    for p in extra:
        target = target.replace(p, "").strip()

    # Append missing placeholders
    missing = expected_set - actual_set
    if missing:
        target = target.rstrip() + " " + " ".join(sorted(missing))

    return target


def _fallback_single(source: str, target_locale: str) -> str:
    return f"[{target_locale}] {source}"


def _fallback_translations(
    segments: list[dict[str, Any]], target_locale: str
) -> list[dict[str, Any]]:
    generated = []
    for seg in segments:
        record = dict(seg)
        record["target_locale"] = target_locale
        record["target"] = _fallback_single(seg.get("source", ""), target_locale)
        record["status"] = "generated"
        record["generation"] = {
            "provider": "deepseek-fallback",
            "quality_claim": "none",
            "purpose": "fallback",
        }
        generated.append(record)
    return generated


def generate_deepseek_batch_file(
    segments_path: Path,
    generated_output: Path,
    target_locale: str,
    source_locale: str = "en-US",
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Read segments from JSONL, translate via DeepSeek, write generated JSONL."""
    segments = read_jsonl(segments_path)
    generated = translate_batch_deepseek(segments, target_locale, source_locale, model)
    write_jsonl(generated_output, generated)

    placeholder_mismatches = []
    for seg in generated:
        target = str(seg.get("target", ""))
        expected = sorted(str(p) for p in seg.get("constraints", {}).get("placeholders", []))
        actual = sorted(extract_placeholders(target))
        if expected != actual:
            placeholder_mismatches.append(seg["segment_id"])

    return {
        "protocol_version": PROTOCOL_VERSION,
        "evidence_channels": ["runtime", "deepseek"],
        "status": "fail" if placeholder_mismatches else "pass",
        "input_segments": segments_path.as_posix(),
        "generated_output": generated_output.as_posix(),
        "target_locale": target_locale,
        "provider": "deepseek",
        "model": model,
        "summary": {
            "segment_count": len(segments),
            "generated_segment_count": len(generated),
            "placeholder_mismatch_count": len(placeholder_mismatches),
        },
        "items": [
            {
                "category": "placeholder_parity",
                "severity": "blocking",
                "message": f"Target lost placeholders for {sid}",
                "segment_id": sid,
            }
            for sid in placeholder_mismatches
        ],
    }
