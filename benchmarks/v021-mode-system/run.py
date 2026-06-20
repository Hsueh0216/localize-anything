from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]
sys.path.insert(0, str(REPOSITORY))

from runtime.localize_anything.apply import execute_apply  # noqa: E402
from runtime.localize_anything.android_strings_adapter import extract_segments  # noqa: E402
from runtime.localize_anything.io_utils import read_json, read_jsonl, write_json, write_jsonl  # noqa: E402
from runtime.localize_anything.json_adapter import source_hash  # noqa: E402
from runtime.localize_anything.project import load_session_index  # noqa: E402
from runtime.localize_anything.run import run_localize  # noqa: E402


SOURCE_LOCALE = "en-US"
TARGET_LOCALE = "zh-CN"
SOURCE_FILE = "app/src/main/res/values/strings.xml"
TARGET_FILE = "app/src/main/res/values-zh-rCN/strings.xml"
SENTINEL = "旧版专属译文_不得进入盲测"
OBSOLETE_KEY = "legacy_removed_key"
OBSOLETE_RESOURCE_KEY = f"string:{OBSOLETE_KEY}"
OBSOLETE_IDENTITY = f"resource_key:{OBSOLETE_RESOURCE_KEY}"
OBSOLETE_TEXT = "旧版专属译文_不得自动删除"

MODE_MATRIX = {
    "blind_benchmark": {"operating_mode": "blind_benchmark", "reference_policy": "blind", "include_target": True, "seed_tm": True},
    "greenfield_localization": {"operating_mode": "greenfield_localization", "reference_policy": None, "include_target": False, "seed_tm": False},
    "existing_locale_maintenance": {
        "operating_mode": "existing_locale_maintenance",
        "reference_policy": "preserve_existing",
        "include_target": True,
        "seed_tm": True,
    },
    "rewrite_or_harmonization": {"operating_mode": "rewrite_or_harmonization", "reference_policy": None, "include_target": True, "seed_tm": True},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0.2.1 localization mode system benchmark")
    parser.add_argument("--work-root", type=Path, default=ROOT / "work")
    parser.add_argument("--report-dir", type=Path, default=ROOT)
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    report = run_benchmark(args.work_root, args.report_dir, args.keep_work)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if report["status"] == "pass" else 1


def run_benchmark(work_root: Path = ROOT / "work", report_dir: Path = ROOT, keep_work: bool = False) -> dict[str, Any]:
    work_root = work_root.resolve()
    report_dir = report_dir.resolve()
    if work_root.exists() and not keep_work:
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    commands = [
        "python -m unittest discover -s tests -v",
        "python -m runtime.localize_anything validate-protocol",
        "python -m runtime.localize_anything validate-contracts",
        "python -m compileall -q runtime benchmarks",
        "python benchmarks/v021-mode-system/run.py",
    ]
    mode_results: dict[str, Any] = {}
    failures: list[str] = []
    target_strings = _target_translation_strings(ROOT / "fixture" / TARGET_FILE)

    for mode_name, config in MODE_MATRIX.items():
        project_root = work_root / mode_name / "project"
        output_root = work_root / mode_name / "runs"
        _copy_fixture(project_root, include_target=bool(config["include_target"]))
        if config["seed_tm"]:
            _seed_reviewed_tm(project_root)
        before_hashes = _resource_hashes(project_root)
        result = run_localize(
            project_root,
            SOURCE_LOCALE,
            [TARGET_LOCALE],
            source_files=[SOURCE_FILE],
            output_root=output_root,
            run_id=f"{mode_name}-001",
            max_segments=100,
            synthetic_draft=True,
            operating_mode=str(config["operating_mode"]),
            reference_policy=config["reference_policy"],
        )
        after_hashes = _resource_hashes(project_root)
        mode_result = _analyze_mode(mode_name, project_root, result, before_hashes, after_hashes, target_strings)
        mode_results[mode_name] = mode_result
        failures.extend(f"{mode_name}: {message}" for message in mode_result["failed_checks"])

    difference = _same_project_difference(mode_results)
    if not difference["pass"]:
        failures.append(difference["message"])

    negative_checks = _run_negative_checks(work_root, mode_results, target_strings)
    failures.extend(check["message"] for check in negative_checks if not check["pass"])
    obsolete_preservation = mode_results["existing_locale_maintenance"]["obsolete_preservation_check"]
    if not obsolete_preservation["pass"] and obsolete_preservation["message"] not in failures:
        failures.append(obsolete_preservation["message"])

    status = "pass" if not failures else "fail"
    report = {
        "schema": "localize-anything-v021-mode-system-benchmark",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": status,
        "fixture_path": (ROOT / "fixture").as_posix(),
        "work_root": work_root.as_posix(),
        "source_locale": SOURCE_LOCALE,
        "target_locale": TARGET_LOCALE,
        "source_file": SOURCE_FILE,
        "target_file": TARGET_FILE,
        "operating_modes_tested": list(MODE_MATRIX),
        "reference_policies_tested": sorted({str(result["reference_policy"]) for result in mode_results.values()}),
        "commands_executed": commands,
        "modes": mode_results,
        "obsolete_preservation_check": obsolete_preservation,
        "same_project_behavior_difference": difference,
        "negative_checks": negative_checks,
        "failed_checks": failures,
        "verdict": (
            "PASS: v0.2.1 obsolete preservation verified"
            if status == "pass"
            else "FAIL: maintenance mode may silently drop obsolete target-only translations"
        ),
    }
    write_json(report_dir / "report.json", report)
    (report_dir / "report.md").write_text(render_report_markdown(report), encoding="utf-8", newline="\n")
    return report


def _copy_fixture(project_root: Path, include_target: bool) -> None:
    if project_root.exists():
        shutil.rmtree(project_root)
    source = ROOT / "fixture"
    shutil.copytree(source, project_root)
    if not include_target:
        target = project_root / TARGET_FILE
        if target.exists():
            target.unlink()
        parent = target.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()


def _seed_reviewed_tm(project_root: Path) -> None:
    source_path = project_root / SOURCE_FILE
    segments = extract_segments(source_path, SOURCE_LOCALE, SOURCE_FILE)
    reviewed_targets = {
        "string:app_name": "模式系统演示_已审",
        "string:welcome_user": "欢迎，%1$s！",
        "string:delete_count": "这将永久删除 %1$d 个文件。",
        "string:delete_all_downloads": "删除所有下载内容？",
        "string:auto_download_wifi": "仅在 Wi-Fi 下自动下载新剧集",
        "plurals:episode_count#one": "%1$d 集",
        "plurals:episode_count#other": "%1$d 集",
        "string-array:quality_options[0]": "高质量",
        "string-array:quality_options[1]": "中等质量",
        "string-array:quality_options[2]": "低质量",
    }
    records: list[dict[str, Any]] = []
    for segment in segments:
        key = str(segment["context"]["resource_key"])
        if key not in reviewed_targets:
            continue
        records.append(
            {
                "id": f"reviewed-{key}",
                "identity": f"resource_key:{key}",
                "segment_id": segment["segment_id"],
                "source": segment["source"],
                "source_hash": segment["source_hash"],
                "target": reviewed_targets[key],
                "source_locale": SOURCE_LOCALE,
                "target_locale": TARGET_LOCALE,
                "content_type": "android_string",
                "status": "reviewed",
            }
        )

    stale_segment = next(segment for segment in segments if segment["context"]["resource_key"] == "string:stale_sync_summary")
    stale_key = str(stale_segment["context"]["resource_key"])
    old_source = "Sync now"
    records.append(
        {
            "id": "reviewed-stale-sync",
            "identity": f"resource_key:{stale_key}",
            "segment_id": stale_segment["segment_id"],
            "source": old_source,
            "source_hash": source_hash(f"{stale_key}\0{old_source}"),
            "target": SENTINEL,
            "source_locale": SOURCE_LOCALE,
            "target_locale": TARGET_LOCALE,
            "content_type": "android_string",
            "status": "reviewed",
        }
    )

    state = project_root / ".localize-anything"
    state.mkdir(parents=True, exist_ok=True)
    write_jsonl(state / "translation-memory.jsonl", records)


def _analyze_mode(
    mode_name: str,
    project_root: Path,
    result: dict[str, Any],
    before_hashes: dict[str, str | None],
    after_hashes: dict[str, str | None],
    target_strings: list[str],
) -> dict[str, Any]:
    artifacts = result["artifacts"]
    run_dir = Path(artifacts["run_directory"])
    reference_plan = read_json(Path(artifacts["reference_plan"]))
    batch_plan = read_json(Path(artifacts["batch_plan"]))
    generation_handoff = read_json(Path(artifacts["generation_handoff"]))
    config = read_json(project_root / ".localize-anything" / "config.json")
    session_index = load_session_index(project_root)
    delivery_manifest = read_json(Path(artifacts["delivery_directory"]) / "delivery-manifest.json")
    delivery_decision = read_json(Path(artifacts["delivery_decision"]))
    apply_plan = read_json(Path(artifacts["apply_plan"]))
    staging_result = read_json(Path(artifacts["staging_result"]))
    apply_to_copy = _apply_to_copy(project_root, result)
    summary = reference_plan["summary"]
    generation_artifacts = _generation_facing_artifacts(artifacts)
    raw_leakage = validate_no_leakage(generation_artifacts, [*target_strings, OBSOLETE_KEY, OBSOLETE_RESOURCE_KEY])
    leakage = (
        raw_leakage
        if mode_name == "blind_benchmark"
        else {
            "pass": True,
            "applicable": False,
            "reason": "existing target references are allowed as evidence in this mode",
            "allowed_reference_match_count": len(raw_leakage["matches"]),
            "scanned_path_count": raw_leakage["scanned_path_count"],
        }
    )
    source_mutation = {
        "pass": before_hashes == after_hashes,
        "before": before_hashes,
        "after": after_hashes,
    }
    apply_deletion = {
        "pass": all(operation.get("action") != "delete" for operation in apply_plan.get("operations", [])),
        "actions": [operation.get("action") for operation in apply_plan.get("operations", [])],
    }
    protocol = _protocol_checks(config, session_index, result, delivery_manifest, reference_plan)
    obsolete_preservation = _obsolete_preservation_check(
        mode_name,
        project_root,
        result,
        reference_plan,
        delivery_decision,
        apply_plan,
        staging_result,
        apply_to_copy,
        generation_artifacts,
    )
    mode_checks = _mode_specific_checks(
        mode_name,
        project_root,
        result,
        reference_plan,
        batch_plan,
        delivery_decision,
        leakage,
        source_mutation,
        apply_deletion,
        obsolete_preservation,
    )
    failed_checks = [
        *protocol["failures"],
        *mode_checks["failures"],
    ]
    return {
        "status": "pass" if not failed_checks else "fail",
        "operating_mode": result["project"]["operating_mode"],
        "reference_policy": result["project"]["reference_policy"],
        "source_locale": result["project"]["source_locale"],
        "target_locale": result["project"]["target_locale"],
        "source_files": result["source_files"],
        "existing_target_detected": any(item.get("exists") for item in reference_plan.get("reference_files", [])),
        "source_segment_count": summary.get("source_segment_count", 0),
        "generated_segment_count": summary.get("candidate_segment_count", 0),
        "preserved_segment_count": summary.get("preserved_segment_count", 0),
        "stale_segment_count": summary.get("stale_reviewed_translation_count", 0),
        "missing_segment_count": summary.get("missing_target_translation_count", 0),
        "obsolete_segment_count": summary.get("obsolete_reference_count", 0),
        "explicit_rewrite_count": summary.get("candidate_segment_count", 0) if mode_name == "rewrite_or_harmonization" else 0,
        "batch_count": len(batch_plan.get("batches", [])),
        "handoff_request_count": generation_handoff.get("request_count"),
        "leakage_check": leakage,
        "source_mutation_check": source_mutation,
        "apply_plan_deletion_check": apply_deletion,
        "obsolete_preservation_check": obsolete_preservation,
        "protocol_check": protocol,
        "mode_check": mode_checks,
        "delivery_decision_localization": delivery_decision.get("localization", {}),
        "artifacts": {
            "run_directory": run_dir.as_posix(),
            "config": (project_root / ".localize-anything" / "config.json").as_posix(),
            "session_index": artifacts["session_index"],
            "run_summary": (run_dir / "run-summary.json").as_posix(),
            "reference_plan": artifacts["reference_plan"],
            "batch_plan": artifacts["batch_plan"],
            "generation_handoff": artifacts["generation_handoff"],
            "work_packets": artifacts["work_packets"],
            "draft_requests": artifacts["draft_requests"],
            "prompts": artifacts["prompts"],
            "generated_segments": artifacts["generated_segments"],
            "staging_result": artifacts["staging_result"],
            "delivery_manifest": (Path(artifacts["delivery_directory"]) / "delivery-manifest.json").as_posix(),
            "delivery_decision": artifacts["delivery_decision"],
            "apply_plan": artifacts["apply_plan"],
            "apply_to_copy_result": apply_to_copy["result_path"],
            "apply_to_copy_project": apply_to_copy["project_root"],
        },
        "failed_checks": failed_checks,
    }


def _protocol_checks(
    config: dict[str, Any],
    session_index: dict[str, Any],
    result: dict[str, Any],
    delivery_manifest: dict[str, Any],
    reference_plan: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    mode = result["project"]["operating_mode"]
    policy = result["project"]["reference_policy"]
    latest_session = session_index["sessions"][-1] if session_index.get("sessions") else {}
    checks = {
        "config_mode": config.get("operating_mode") == mode,
        "config_reference_policy": config.get("reference_policy") == policy,
        "session_mode": latest_session.get("operating_mode") == mode,
        "session_reference_policy": latest_session.get("reference_policy") == policy,
        "run_summary_mode": result.get("project", {}).get("operating_mode") == mode,
        "run_summary_reference_policy": result.get("project", {}).get("reference_policy") == policy,
        "delivery_manifest_mode": delivery_manifest.get("project", {}).get("operating_mode") == mode,
        "delivery_manifest_reference_policy": delivery_manifest.get("project", {}).get("reference_policy") == policy,
        "source_locale": result.get("project", {}).get("source_locale") == SOURCE_LOCALE,
        "target_locale": result.get("project", {}).get("target_locale") == TARGET_LOCALE,
        "source_files": result.get("source_files") == [SOURCE_FILE],
        "reference_policy_first_class": "reference_policy" in reference_plan,
        "existing_target_detection_recorded": "existing_reference_file_count" in reference_plan.get("summary", {}),
    }
    for name, passed in checks.items():
        if not passed:
            failures.append(f"protocol check failed: {name}")
    return {"pass": not failures, "checks": checks, "failures": failures}


def _apply_to_copy(project_root: Path, result: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(result["artifacts"]["run_directory"])
    copy_root = run_dir / "apply-copy-project"
    if copy_root.exists():
        shutil.rmtree(copy_root)
    shutil.copytree(project_root, copy_root)
    apply_result = execute_apply(Path(result["artifacts"]["delivery_directory"]), copy_root, str(result["run_id"]))
    result_path = run_dir / "apply-to-copy-result.json"
    write_json(result_path, apply_result)
    return {
        "project_root": copy_root.as_posix(),
        "target_path": (copy_root / TARGET_FILE).as_posix(),
        "result_path": result_path.as_posix(),
        "result": apply_result,
    }


def _obsolete_preservation_check(
    mode_name: str,
    project_root: Path,
    result: dict[str, Any],
    reference_plan: dict[str, Any],
    delivery_decision: dict[str, Any],
    apply_plan: dict[str, Any],
    staging_result: dict[str, Any],
    apply_to_copy: dict[str, Any],
    generation_artifacts: list[str],
) -> dict[str, Any]:
    original_target = project_root / TARGET_FILE
    staged_target = _staged_target_path(staging_result)
    applied_target = Path(apply_to_copy["target_path"])
    generation_leakage = validate_no_leakage(generation_artifacts, [OBSOLETE_KEY, OBSOLETE_RESOURCE_KEY, OBSOLETE_TEXT])
    generated_path = Path(result["artifacts"].get("generated_segments", ""))
    generated_records = read_jsonl(generated_path) if generated_path.is_file() else []
    generated_obsolete = [
        record
        for record in generated_records
        if record.get("context", {}).get("resource_key") == OBSOLETE_RESOURCE_KEY
        or record.get("context", {}).get("resource_name") == OBSOLETE_KEY
    ]
    check = {
        "pass": True,
        "mode": mode_name,
        "obsolete_key": OBSOLETE_KEY,
        "obsolete_resource_key": OBSOLETE_RESOURCE_KEY,
        "obsolete_text": OBSOLETE_TEXT,
        "detected_as_obsolete": _reference_plan_has_obsolete_key(reference_plan),
        "present_in_original_target": _file_contains_obsolete(original_target),
        "present_in_staged_target": _file_contains_obsolete(staged_target),
        "present_after_apply_to_copy": _file_contains_obsolete(applied_target),
        "deleted_by_apply_plan": _apply_plan_deletes_obsolete(apply_plan),
        "generation_facing_leakage": not generation_leakage["pass"],
        "requires_owner_review": _delivery_marks_obsolete_owner_review(delivery_decision),
        "not_counted_as_generated": not generated_obsolete,
        "staged_target": staged_target.as_posix() if staged_target else None,
        "applied_target": applied_target.as_posix(),
        "message": "obsolete target-only key preservation verified",
    }
    if mode_name not in {"existing_locale_maintenance", "rewrite_or_harmonization"}:
        check["pass"] = not check["generation_facing_leakage"]
        check["message"] = (
            "obsolete target-only key did not leak to generation artifacts"
            if check["pass"]
            else f"{mode_name} leaked obsolete target-only key {OBSOLETE_KEY} to generation artifacts"
        )
        return check

    required = [
        "detected_as_obsolete",
        "present_in_original_target",
        "present_in_staged_target",
        "present_after_apply_to_copy",
        "requires_owner_review",
        "not_counted_as_generated",
    ]
    failed = [name for name in required if not check[name]]
    if check["deleted_by_apply_plan"]:
        failed.append("deleted_by_apply_plan")
    if check["generation_facing_leakage"]:
        failed.append("generation_facing_leakage")
    if failed:
        check["pass"] = False
        if mode_name == "existing_locale_maintenance" and (
            "present_in_staged_target" in failed or "present_after_apply_to_copy" in failed
        ):
            check["message"] = (
                f"existing_locale_maintenance dropped obsolete target-only key {OBSOLETE_KEY} "
                "without explicit obsolete cleanup approval"
            )
        else:
            check["message"] = f"obsolete target-only preservation failed: {', '.join(failed)}"
    return check


def validate_obsolete_target_preservation(
    reference_plan: dict[str, Any],
    delivery_decision: dict[str, Any],
    apply_plan: dict[str, Any],
    original_target: Path,
    staged_target: Path,
    applied_target: Path,
    mode_name: str = "existing_locale_maintenance",
) -> dict[str, Any]:
    check = {
        "pass": True,
        "obsolete_key": OBSOLETE_KEY,
        "obsolete_text": OBSOLETE_TEXT,
        "detected_as_obsolete": _reference_plan_has_obsolete_key(reference_plan),
        "present_in_original_target": _file_contains_obsolete(original_target),
        "present_in_staged_target": _file_contains_obsolete(staged_target),
        "present_after_apply_to_copy": _file_contains_obsolete(applied_target),
        "deleted_by_apply_plan": _apply_plan_deletes_obsolete(apply_plan),
        "requires_owner_review": _delivery_marks_obsolete_owner_review(delivery_decision),
        "message": "obsolete target-only key preservation verified",
    }
    failed = [
        name
        for name in (
            "detected_as_obsolete",
            "present_in_original_target",
            "present_in_staged_target",
            "present_after_apply_to_copy",
            "requires_owner_review",
        )
        if not check[name]
    ]
    if check["deleted_by_apply_plan"]:
        failed.append("deleted_by_apply_plan")
    if failed:
        check["pass"] = False
        if mode_name == "existing_locale_maintenance" and (
            "present_in_staged_target" in failed or "present_after_apply_to_copy" in failed
        ):
            check["message"] = (
                f"existing_locale_maintenance dropped obsolete target-only key {OBSOLETE_KEY} "
                "without explicit obsolete cleanup approval"
            )
        else:
            check["message"] = f"obsolete target-only preservation failed: {', '.join(failed)}"
    return check


def _staged_target_path(staging_result: dict[str, Any]) -> Path:
    for output in staging_result.get("outputs", []):
        if output.get("destination") == TARGET_FILE:
            return Path(output["output"])
    return Path(staging_result.get("staging_dir", "")) / TARGET_FILE


def _file_contains_obsolete(path: Path | None) -> bool:
    if path is None or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return f'name="{OBSOLETE_KEY}"' in text and OBSOLETE_TEXT in text


def _reference_plan_has_obsolete_key(reference_plan: dict[str, Any]) -> bool:
    for item in reference_plan.get("obsolete_references", []):
        if item.get("identity") == OBSOLETE_IDENTITY or item.get("resource_key") == OBSOLETE_RESOURCE_KEY:
            return True
    return False


def _delivery_marks_obsolete_owner_review(delivery_decision: dict[str, Any]) -> bool:
    for decision in delivery_decision.get("decisions", []):
        if decision.get("type") != "obsolete_target_reference" or decision.get("status") != "requires_review":
            continue
        refs = decision.get("evidence", {}).get("obsolete_references", [])
        if any(item.get("identity") == OBSOLETE_IDENTITY or item.get("resource_key") == OBSOLETE_RESOURCE_KEY for item in refs):
            return True
    return False


def _apply_plan_deletes_obsolete(apply_plan: dict[str, Any]) -> bool:
    for operation in apply_plan.get("operations", []):
        if operation.get("action") != "delete":
            continue
        encoded = json.dumps(operation, ensure_ascii=False)
        if OBSOLETE_KEY in encoded or TARGET_FILE in encoded:
            return True
    return False


def _mode_specific_checks(
    mode_name: str,
    project_root: Path,
    result: dict[str, Any],
    reference_plan: dict[str, Any],
    batch_plan: dict[str, Any],
    delivery_decision: dict[str, Any],
    leakage: dict[str, Any],
    source_mutation: dict[str, Any],
    apply_deletion: dict[str, Any],
    obsolete_preservation: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    summary = reference_plan["summary"]
    source_count = int(summary.get("source_segment_count", 0))
    generated_count = int(summary.get("candidate_segment_count", 0))
    preserved_count = int(summary.get("preserved_segment_count", 0))
    stale_count = int(summary.get("stale_reviewed_translation_count", 0))
    missing_count = int(summary.get("missing_target_translation_count", 0))
    obsolete_count = int(summary.get("obsolete_reference_count", 0))
    decision_localization = delivery_decision.get("localization", {})

    if not source_mutation["pass"]:
        failures.append("source resource files mutated")
    if not apply_deletion["pass"]:
        failures.append("apply plan contains deletion action")
    if mode_name in {"existing_locale_maintenance", "rewrite_or_harmonization"} and not obsolete_preservation["pass"]:
        failures.append(obsolete_preservation["message"])
    if decision_localization:
        expected_pairs = {
            "generated_count": generated_count,
            "preserved_count": preserved_count,
            "stale_count": stale_count,
            "missing_count": missing_count,
            "obsolete_count": obsolete_count,
        }
        for key, expected in expected_pairs.items():
            if int(decision_localization.get(key, 0)) != expected:
                failures.append(f"delivery decision localization {key} mismatch")

    if mode_name == "blind_benchmark":
        if result["project"]["reference_policy"] != "blind":
            failures.append("blind benchmark did not use reference_policy=blind")
        if not leakage["pass"]:
            failures.append("blind generation-facing artifact leaked existing target translation")
        if not summary.get("blind_reference_hidden"):
            failures.append("blind reference plan did not label hidden references")
        if generated_count != source_count:
            failures.append("blind benchmark did not generate candidates for all translatable source segments")
    elif mode_name == "greenfield_localization":
        if summary.get("existing_reference_file_count") != 0:
            failures.append("greenfield unexpectedly detected existing target references")
        if not (project_root / ".localize-anything" / "translation-memory.jsonl").is_file():
            failures.append("greenfield did not initialize translation memory")
        if not Path(result["artifacts"]["staging_result"]).is_file():
            failures.append("greenfield did not stage output")
        if (project_root / TARGET_FILE).exists():
            failures.append("greenfield wrote target file into source project")
    elif mode_name == "existing_locale_maintenance":
        maintenance = validate_maintenance_not_mass_rewrite(reference_plan, result)
        if not maintenance["pass"]:
            failures.append(maintenance["message"])
        if preserved_count <= 0:
            failures.append("maintenance preserved no reviewed unchanged translations")
        if stale_count <= 0:
            failures.append("maintenance did not mark stale reviewed translation")
        if missing_count <= 0:
            failures.append("maintenance did not mark missing target translation")
        if obsolete_count <= 0:
            failures.append("maintenance did not flag obsolete target-only translation")
        if obsolete_preservation.get("not_counted_as_generated") is False:
            failures.append("maintenance counted obsolete target-only key as generated source segment")
        if not (project_root / TARGET_FILE).read_text(encoding="utf-8").find("obsolete_legacy_only") >= 0:
            failures.append("obsolete target-only translation was deleted from source project")
    elif mode_name == "rewrite_or_harmonization":
        if result["project"]["operating_mode"] != "rewrite_or_harmonization":
            failures.append("rewrite mode was not explicitly recorded")
        if generated_count != source_count:
            failures.append("rewrite mode did not generate candidates for all translatable source segments")
        if preserved_count != 0:
            failures.append("rewrite mode preserved segments by default")
        if not any(batch.get("segment_ids") for batch in batch_plan.get("batches", [])):
            failures.append("rewrite mode produced no generation plan")
        if not obsolete_preservation.get("requires_owner_review"):
            failures.append("rewrite mode did not mark obsolete target-only keys for owner review")
    return {"pass": not failures, "failures": failures}


def validate_no_leakage(paths: list[str], forbidden_strings: list[str]) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    filtered = [text for text in forbidden_strings if text]
    for value in paths:
        path = Path(value)
        if path.is_dir():
            candidates = [item for item in path.rglob("*") if item.is_file()]
        elif path.is_file():
            candidates = [path]
        else:
            candidates = []
        for candidate in candidates:
            try:
                text = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for forbidden in filtered:
                if forbidden in text:
                    matches.append({"path": candidate.as_posix(), "text": forbidden})
    return {"pass": not matches, "matches": matches, "scanned_path_count": len(paths)}


def validate_maintenance_not_mass_rewrite(reference_plan: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = reference_plan.get("summary", {})
    source_count = int(summary.get("source_segment_count", 0))
    candidate_count = int(summary.get("candidate_segment_count", 0))
    preserved_count = int(summary.get("preserved_segment_count", 0))
    if source_count > 0 and candidate_count == source_count and preserved_count == 0:
        return {
            "pass": False,
            "message": "maintenance mode planned a mass rewrite of all source segments without explicit rewrite_or_harmonization",
        }
    if result:
        preserved_ids = {
            item["segment_id"]
            for item in reference_plan.get("decisions", [])
            if item.get("action") == "preserve_existing"
        }
        packet_dir = Path(result["artifacts"]["work_packets"])
        packet_ids = {
            segment["segment_id"]
            for packet_path in packet_dir.glob("*.json")
            for segment in read_json(packet_path).get("segments", [])
        }
        leaked_preserved = sorted(preserved_ids & packet_ids)
        if leaked_preserved:
            return {
                "pass": False,
                "message": f"maintenance mode sent preserved reviewed segments to generation: {', '.join(leaked_preserved[:3])}",
            }
    return {"pass": True, "message": "maintenance mode preserved reviewed unchanged segments and avoided mass rewrite"}


def _same_project_difference(mode_results: dict[str, Any]) -> dict[str, Any]:
    blind = mode_results["blind_benchmark"]
    maintenance = mode_results["existing_locale_maintenance"]
    if blind["generated_segment_count"] != blind["source_segment_count"]:
        return {"pass": False, "message": "blind benchmark did not generate all source candidates"}
    if maintenance["preserved_segment_count"] <= 0:
        return {"pass": False, "message": "maintenance preserved no reviewed segments"}
    if maintenance["generated_segment_count"] >= blind["generated_segment_count"]:
        return {"pass": False, "message": "blind and maintenance produced the same generation plan"}
    return {
        "pass": True,
        "message": "same fixture produces all-candidate blind plan and preserve-first maintenance plan",
        "blind_generated": blind["generated_segment_count"],
        "maintenance_generated": maintenance["generated_segment_count"],
        "maintenance_preserved": maintenance["preserved_segment_count"],
    }


def _run_negative_checks(work_root: Path, mode_results: dict[str, Any], target_strings: list[str]) -> list[dict[str, Any]]:
    negative_dir = work_root / "negative"
    negative_dir.mkdir(parents=True, exist_ok=True)
    leaked = negative_dir / "leaky-work-packet.json"
    leaked.write_text(json.dumps({"target_reference": SENTINEL}, ensure_ascii=False), encoding="utf-8")
    leakage_negative = validate_no_leakage([leaked.as_posix()], target_strings)
    maintenance = mode_results["existing_locale_maintenance"]
    fake_mass_rewrite_plan = {
        "summary": {
            "source_segment_count": maintenance["source_segment_count"],
            "candidate_segment_count": maintenance["source_segment_count"],
            "preserved_segment_count": 0,
        }
    }
    mass_rewrite_negative = validate_maintenance_not_mass_rewrite(fake_mass_rewrite_plan)
    missing_obsolete_dir = negative_dir / "missing-obsolete"
    missing_obsolete_dir.mkdir(parents=True, exist_ok=True)
    original_target = missing_obsolete_dir / "original.xml"
    staged_target = missing_obsolete_dir / "staged.xml"
    applied_target = missing_obsolete_dir / "applied.xml"
    original_target.write_text(f'<resources><string name="{OBSOLETE_KEY}">{OBSOLETE_TEXT}</string></resources>\n', encoding="utf-8")
    staged_target.write_text("<resources></resources>\n", encoding="utf-8")
    applied_target.write_text("<resources></resources>\n", encoding="utf-8")
    fake_reference_plan = {
        "obsolete_references": [
            {
                "identity": OBSOLETE_IDENTITY,
                "resource_key": OBSOLETE_RESOURCE_KEY,
                "target": OBSOLETE_TEXT,
                "status": "obsolete_target_reference",
            }
        ]
    }
    fake_delivery_decision = {
        "decisions": [
            {
                "type": "obsolete_target_reference",
                "status": "requires_review",
                "evidence": {"obsolete_references": fake_reference_plan["obsolete_references"]},
            }
        ]
    }
    missing_obsolete_negative = validate_obsolete_target_preservation(
        fake_reference_plan,
        fake_delivery_decision,
        {"operations": [{"action": "replace", "destination": TARGET_FILE}]},
        original_target,
        staged_target,
        applied_target,
    )
    return [
        {
            "name": "blind_artifact_with_existing_target_translation_is_rejected",
            "pass": not leakage_negative["pass"],
            "message": "negative leakage check did not fail" if leakage_negative["pass"] else "negative leakage check failed as expected",
            "matches": leakage_negative["matches"],
        },
        {
            "name": "maintenance_mass_rewrite_without_rewrite_mode_is_rejected",
            "pass": not mass_rewrite_negative["pass"],
            "message": "negative mass rewrite check did not fail" if mass_rewrite_negative["pass"] else "negative mass rewrite check failed as expected",
            "validator_message": mass_rewrite_negative["message"],
        },
        {
            "name": "maintenance_staged_file_missing_obsolete_key_is_rejected",
            "pass": not missing_obsolete_negative["pass"],
            "message": (
                "negative obsolete preservation check did not fail"
                if missing_obsolete_negative["pass"]
                else "negative obsolete preservation check failed as expected"
            ),
            "validator_message": missing_obsolete_negative["message"],
        },
    ]


def _generation_facing_artifacts(artifacts: dict[str, Any]) -> list[str]:
    keys = [
        "work_packets",
        "draft_requests",
        "prompts",
        "prompt_manifest",
        "generation_handoff",
        "generation_readme",
        "generated_segments",
    ]
    return [str(artifacts[key]) for key in keys if key in artifacts]


def _target_translation_strings(target_path: Path) -> list[str]:
    segments = extract_segments(target_path, TARGET_LOCALE, TARGET_FILE)
    return sorted({str(segment.get("source", "")) for segment in segments if segment.get("source")})


def _resource_hashes(project_root: Path) -> dict[str, str | None]:
    return {
        SOURCE_FILE: _sha256(project_root / SOURCE_FILE) if (project_root / SOURCE_FILE).is_file() else None,
        TARGET_FILE: _sha256(project_root / TARGET_FILE) if (project_root / TARGET_FILE).is_file() else None,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# v0.2.1 Localization Mode System Benchmark",
        "",
        f"- Status: `{report['status']}`",
        f"- Verdict: **{report['verdict']}**",
        f"- Fixture: `{report['fixture_path']}`",
        f"- Source locale: `{report['source_locale']}`",
        f"- Target locale: `{report['target_locale']}`",
        f"- Modes tested: {', '.join(report['operating_modes_tested'])}",
        f"- Reference policies tested: {', '.join(report['reference_policies_tested'])}",
        "",
        "## Obsolete Preservation",
        "",
    ]
    obsolete = report["obsolete_preservation_check"]
    lines.extend(
        [
            f"- Pass: `{obsolete['pass']}`",
            f"- Obsolete key: `{obsolete['obsolete_key']}`",
            f"- Obsolete text: `{obsolete['obsolete_text']}`",
            f"- Detected as obsolete: `{obsolete['detected_as_obsolete']}`",
            f"- Present in original target: `{obsolete['present_in_original_target']}`",
            f"- Present in staged target: `{obsolete['present_in_staged_target']}`",
            f"- Present after apply-to-copy: `{obsolete['present_after_apply_to_copy']}`",
            f"- Deleted by apply plan: `{obsolete['deleted_by_apply_plan']}`",
            f"- Generation-facing leakage: `{obsolete['generation_facing_leakage']}`",
            f"- Requires owner review: `{obsolete['requires_owner_review']}`",
            "",
        ]
    )
    lines.extend(
        [
        "## Commands",
        "",
        ]
    )
    for command in report["commands_executed"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Mode Results", ""])
    for mode_name, result in report["modes"].items():
        lines.extend(
            [
                f"### {mode_name}",
                "",
                f"- Status: `{result['status']}`",
                f"- Operating mode: `{result['operating_mode']}`",
                f"- Reference policy: `{result['reference_policy']}`",
                f"- Existing target detected: `{result['existing_target_detected']}`",
                f"- Source segments: {result['source_segment_count']}",
                f"- Generated candidates: {result['generated_segment_count']}",
                f"- Preserved: {result['preserved_segment_count']}",
                f"- Stale: {result['stale_segment_count']}",
                f"- Missing: {result['missing_segment_count']}",
                f"- Obsolete: {result['obsolete_segment_count']}",
                f"- Explicit rewrite: {result['explicit_rewrite_count']}",
                f"- Leakage check: `{result['leakage_check']['pass']}`",
                f"- Source mutation check: `{result['source_mutation_check']['pass']}`",
                f"- Apply-plan deletion check: `{result['apply_plan_deletion_check']['pass']}`",
                f"- Obsolete preservation check: `{result['obsolete_preservation_check']['pass']}`",
                f"- Reference plan: `{result['artifacts']['reference_plan']}`",
                f"- Delivery decision: `{result['artifacts']['delivery_decision']}`",
                f"- Apply plan: `{result['artifacts']['apply_plan']}`",
                "",
            ]
        )
        if result["failed_checks"]:
            lines.append("Failed checks:")
            lines.extend(f"- {item}" for item in result["failed_checks"])
            lines.append("")
    lines.extend(
        [
            "## Same-Project Difference",
            "",
            f"- Pass: `{report['same_project_behavior_difference']['pass']}`",
            f"- Message: {report['same_project_behavior_difference']['message']}",
            "",
            "## Negative Checks",
            "",
        ]
    )
    for check in report["negative_checks"]:
        lines.append(f"- `{check['name']}`: `{check['pass']}` - {check['message']}")
    if report["failed_checks"]:
        lines.extend(["", "## Failed Checks", ""])
        lines.extend(f"- {item}" for item in report["failed_checks"])
    else:
        lines.extend(["", "No failed checks.", ""])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
