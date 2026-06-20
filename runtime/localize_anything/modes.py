from __future__ import annotations

from typing import Any


REFERENCE_POLICIES = ("blind", "style_only", "tm_assisted", "preserve_existing")
OPERATING_MODES = (
    "blind_benchmark",
    "greenfield_localization",
    "existing_locale_maintenance",
    "rewrite_or_harmonization",
)

DEFAULT_OPERATING_MODE = "greenfield_localization"
DEFAULT_REFERENCE_POLICY_BY_MODE = {
    "blind_benchmark": "blind",
    "greenfield_localization": "style_only",
    "existing_locale_maintenance": "preserve_existing",
    "rewrite_or_harmonization": "tm_assisted",
}


def resolve_mode_policy(operating_mode: str | None = None, reference_policy: str | None = None) -> tuple[str, str]:
    mode = operating_mode or DEFAULT_OPERATING_MODE
    if mode not in OPERATING_MODES:
        raise ValueError(f"Unsupported operating_mode: {mode}")
    policy = reference_policy or DEFAULT_REFERENCE_POLICY_BY_MODE[mode]
    if policy not in REFERENCE_POLICIES:
        raise ValueError(f"Unsupported reference_policy: {policy}")
    if mode == "blind_benchmark" and policy != "blind":
        raise ValueError("blind_benchmark requires reference_policy=blind")
    if mode == "existing_locale_maintenance" and policy == "blind":
        raise ValueError("existing_locale_maintenance cannot use reference_policy=blind")
    return mode, policy


def mode_contract(operating_mode: str, reference_policy: str) -> dict[str, Any]:
    return {
        "operating_mode": operating_mode,
        "reference_policy": reference_policy,
        "source_truth": "source_locale_files",
        "target_reference_visibility": _target_reference_visibility(reference_policy),
        "generation_scope": _generation_scope(operating_mode, reference_policy),
    }


def _target_reference_visibility(reference_policy: str) -> str:
    if reference_policy == "blind":
        return "hidden_from_generation"
    if reference_policy == "style_only":
        return "style_and_terminology_only"
    if reference_policy == "tm_assisted":
        return "approved_translation_memory_only"
    return "approved_preservation_and_translation_memory"


def _generation_scope(operating_mode: str, reference_policy: str) -> str:
    if operating_mode == "existing_locale_maintenance" and reference_policy == "preserve_existing":
        return "missing_stale_conflicting_or_user_selected_segments"
    if operating_mode == "blind_benchmark":
        return "all_selected_source_segments_without_target_references"
    return "all_selected_source_segments"
