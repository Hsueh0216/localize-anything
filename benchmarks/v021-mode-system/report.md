# v0.2.1 Localization Mode System Benchmark

- Status: `pass`
- Verdict: **PASS: v0.2.1 obsolete preservation verified**
- Fixture: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/fixture`
- Source locale: `en-US`
- Target locale: `zh-CN`
- Modes tested: blind_benchmark, greenfield_localization, existing_locale_maintenance, rewrite_or_harmonization
- Reference policies tested: blind, preserve_existing, style_only, tm_assisted

## Obsolete Preservation

- Pass: `True`
- Obsolete key: `legacy_removed_key`
- Obsolete text: `旧版专属译文_不得自动删除`
- Detected as obsolete: `True`
- Present in original target: `True`
- Present in staged target: `True`
- Present after apply-to-copy: `True`
- Deleted by apply plan: `False`
- Generation-facing leakage: `False`
- Requires owner review: `True`

## Commands

- `python -m unittest discover -s tests -v`
- `python -m runtime.localize_anything validate-protocol`
- `python -m runtime.localize_anything validate-contracts`
- `python -m compileall -q runtime benchmarks`
- `python benchmarks/v021-mode-system/run.py`

## Mode Results

### blind_benchmark

- Status: `pass`
- Operating mode: `blind_benchmark`
- Reference policy: `blind`
- Existing target detected: `True`
- Source segments: 12
- Generated candidates: 12
- Preserved: 0
- Stale: 1
- Missing: 1
- Obsolete: 2
- Explicit rewrite: 0
- Leakage check: `True`
- Source mutation check: `True`
- Apply-plan deletion check: `True`
- Obsolete preservation check: `True`
- Reference plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/blind_benchmark/runs/blind_benchmark-001/reference-plan.json`
- Delivery decision: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/blind_benchmark/runs/blind_benchmark-001/delivery-decision.json`
- Apply plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/blind_benchmark/runs/blind_benchmark-001/apply-plan.json`

### greenfield_localization

- Status: `pass`
- Operating mode: `greenfield_localization`
- Reference policy: `style_only`
- Existing target detected: `False`
- Source segments: 12
- Generated candidates: 12
- Preserved: 0
- Stale: 0
- Missing: 12
- Obsolete: 0
- Explicit rewrite: 0
- Leakage check: `True`
- Source mutation check: `True`
- Apply-plan deletion check: `True`
- Obsolete preservation check: `True`
- Reference plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/greenfield_localization/runs/greenfield_localization-001/reference-plan.json`
- Delivery decision: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/greenfield_localization/runs/greenfield_localization-001/delivery-decision.json`
- Apply plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/greenfield_localization/runs/greenfield_localization-001/apply-plan.json`

### existing_locale_maintenance

- Status: `pass`
- Operating mode: `existing_locale_maintenance`
- Reference policy: `preserve_existing`
- Existing target detected: `True`
- Source segments: 12
- Generated candidates: 2
- Preserved: 10
- Stale: 1
- Missing: 1
- Obsolete: 2
- Explicit rewrite: 0
- Leakage check: `True`
- Source mutation check: `True`
- Apply-plan deletion check: `True`
- Obsolete preservation check: `True`
- Reference plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/existing_locale_maintenance/runs/existing_locale_maintenance-001/reference-plan.json`
- Delivery decision: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/existing_locale_maintenance/runs/existing_locale_maintenance-001/delivery-decision.json`
- Apply plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/existing_locale_maintenance/runs/existing_locale_maintenance-001/apply-plan.json`

### rewrite_or_harmonization

- Status: `pass`
- Operating mode: `rewrite_or_harmonization`
- Reference policy: `tm_assisted`
- Existing target detected: `True`
- Source segments: 12
- Generated candidates: 12
- Preserved: 0
- Stale: 1
- Missing: 1
- Obsolete: 2
- Explicit rewrite: 12
- Leakage check: `True`
- Source mutation check: `True`
- Apply-plan deletion check: `True`
- Obsolete preservation check: `True`
- Reference plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/rewrite_or_harmonization/runs/rewrite_or_harmonization-001/reference-plan.json`
- Delivery decision: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/rewrite_or_harmonization/runs/rewrite_or_harmonization-001/delivery-decision.json`
- Apply plan: `/mnt/c/Users/eliot/Documents/localize-anything/benchmarks/v021-mode-system/work/rewrite_or_harmonization/runs/rewrite_or_harmonization-001/apply-plan.json`

## Same-Project Difference

- Pass: `True`
- Message: same fixture produces all-candidate blind plan and preserve-first maintenance plan

## Negative Checks

- `blind_artifact_with_existing_target_translation_is_rejected`: `True` - negative leakage check failed as expected
- `maintenance_mass_rewrite_without_rewrite_mode_is_rejected`: `True` - negative mass rewrite check failed as expected
- `maintenance_staged_file_missing_obsolete_key_is_rejected`: `True` - negative obsolete preservation check failed as expected

No failed checks.

