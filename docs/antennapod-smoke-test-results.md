# AntennaPod Smoke Test Results

## Summary

This was a disposable-clone smoke test against AntennaPod. AntennaPod was cloned
outside this repository and was not vendored. Generated outputs, delivery
packages, review sheets, and temporary evidence files were kept outside this
repository and were not committed.

The test focused on workflow safety, source/resource detection, deterministic
evidence, staging, review artifacts, and delivery packaging. It did not evaluate
translation quality. No destructive apply step was run.

## Environment

- Date: 2026-06-21
- OS / shell: Windows PowerShell, with Git for Windows Bash used for the helper script
- Python: 3.14.0
- Localize Anything commit: `db57a3a4e452f913dc1677b66c4584c6fc26b930`
- Localize Anything package version: `0.2.4`
- Localize Anything protocol version: `0.1`
- AntennaPod commit: `f7f0314888631208fedb26518fd924cb7805062f`
- AntennaPod clone location policy: temporary directory outside this repository
- Evidence output policy: temporary directory outside this repository

## Commands Run

The temporary root was created under the OS temp directory as
`$env:TEMP/localize-anything-antennapod-smoke-<id>`. The concrete local path is
machine-specific and was not copied into this repository.

```powershell
git fetch origin --tags
git switch main
git pull --ff-only origin main
git switch -c docs/antennapod-smoke-results

git clone --depth 1 https://github.com/AntennaPod/AntennaPod.git "$tmpRoot/AntennaPod"
git -C "$tmpRoot/AntennaPod" rev-parse HEAD
git -C "$tmpRoot/AntennaPod" status --short --untracked-files=all

git rev-parse HEAD
python --version
python -c "import runtime.localize_anything as la; print('runtime version:', getattr(la, '__version__', 'unknown')); print('protocol version:', getattr(la, 'PROTOCOL_VERSION', 'unknown'))"
python -m runtime.localize_anything --help

bash -n scripts/smoke-antennapod.sh
python -m runtime.localize_anything localize-run --help
```

The default `bash` on this machine was WSL Bash and failed `bash -n` on the
checked-out helper because of CRLF line endings. A temporary LF-normalized copy
of the helper was created, run with Git for Windows Bash from the repository's
`scripts/` directory, then removed before committing:

```powershell
& "C:\Program Files\Git\bin\bash.exe" -n scripts/smoke-antennapod.lf.tmp.sh
& "C:\Program Files\Git\bin\bash.exe" scripts/smoke-antennapod.lf.tmp.sh `
  /tmp/localize-anything-antennapod-smoke-<id>/AntennaPod `
  /tmp/localize-anything-antennapod-smoke-<id>/evidence-helper
```

The documented synthetic blind pipeline was then run against the disposable
clone, with outputs outside both repositories:

```powershell
python -m runtime.localize_anything localize-run "$tmpRoot/AntennaPod" `
  --source-locale en-US `
  --target-locale zh-CN `
  --source-file ui/i18n/src/main/res/values/strings.xml `
  --output-root "$tmpRoot/evidence-full/runs" `
  --run-id antennapod-blind-smoke `
  --synthetic-draft `
  --operating-mode blind_benchmark `
  --reference-policy blind `
  --workflow-depth standard `
  --output "$tmpRoot/evidence-full/run-summary.json"
```

Source mutation and repository validation commands:

```powershell
git -C "$tmpRoot/AntennaPod" status --short --untracked-files=all
git -C "$tmpRoot/AntennaPod" status --short --untracked-files=no
git -C "$tmpRoot/AntennaPod" diff --exit-code

python -m unittest discover -s tests -v
python -m runtime.localize_anything validate-protocol
python -m runtime.localize_anything validate-contracts
python -m compileall -q runtime benchmarks
python benchmarks/v022-android-resource-reliability/run.py
python benchmarks/v022-android-resource-reliability/source_sets.py
python benchmarks/v022-android-resource-reliability/risk_classification.py
python benchmarks/v021-mode-system/run.py
```

## Results

- Helper result: passed after using an LF-normalized temporary copy with Git for
  Windows Bash.
- Available CLI commands confirmed: `inspect`, `localize-run`, `validate-protocol`,
  `validate-contracts`, `review-sheet`, `delivery-decision`, `apply-delivery`,
  and other adapter/runtime commands were present in `--help`.
- Android project/resource detection succeeded.
- Inspection evidence:
  - `supported_file_count`: 125
  - Android generation source files: 1
  - Android generation source file:
    `ui/i18n/src/main/res/values/strings.xml`
  - Android locale reference files: 52
  - Non-text assets reported for review: 67
  - Recommended preflight mode: `layered`
  - Recommended workflow depth: `standard`
- Full synthetic blind pipeline evidence:
  - Run status: `draft_package_created`
  - Source file: `ui/i18n/src/main/res/values/strings.xml`
  - Segments extracted: 869
  - Synthetic generated segments: 869
  - Batch count: 11
  - Staging status: `pass`
  - Staged output destination:
    `ui/i18n/src/main/res/values-zh-rCN/strings.xml`
  - Android source set: `main`
  - Android source resource directory: `values`
  - Target resource directory: `values-zh-rCN`
  - Delivery status: `draft_package`
  - Delivery decision: `owner_review_required`
  - QA status: `pass_with_warnings`
  - QA blocking issues: 0
  - QA warnings: 2 `comment_missing` warnings in staged output
  - Unprocessed assets in delivery dashboard: 67
  - Review artifacts created externally: JSON, Markdown, and CSV review sheets
  - Delivery artifacts created externally: delivery manifest, dashboard,
    delivery decision, apply plan, and packaged staged file
  - Risk metadata appeared in generated/work-packet artifacts.
- Generated artifacts were created only under the temporary evidence directory
  outside this repository. They were not committed.
- No destructive apply command was executed.
- Validation gates all passed. `compileall` exited 0; known Windows historical
  benchmark work-dir warnings are acceptable for this repository.

## Source Mutation Check

Before the smoke test, AntennaPod `git status --short --untracked-files=all`
returned no entries.

The read-only helper preserved AntennaPod status with no tracked or untracked
changes.

The full synthetic `localize-run` created expected untracked Localize Anything
project state in the disposable clone:

```text
?? .localize-anything/config.json
?? .localize-anything/delivery-manifest.json
?? .localize-anything/glossary.csv
?? .localize-anything/localization-context.md
?? .localize-anything/sessions/index.json
?? .localize-anything/translation-memory.jsonl
```

Tracked AntennaPod source files were not modified:

```text
git -C "$tmpRoot/AntennaPod" status --short --untracked-files=no
# no output

git -C "$tmpRoot/AntennaPod" diff --exit-code
# exit 0
```

The temporary `.localize-anything/` state was removed from the disposable clone
after recording the summary. Final AntennaPod status was clean.

## Not Executed

- Destructive apply was not executed.
- `apply-delivery` was not executed.
- Production translation generation was not executed.
- Network/model-provider translation was not executed.
- AntennaPod build or APK validation was not executed.

These steps were skipped because this run was scoped to non-destructive workflow
evidence and synthetic draft generation. Translation quality and app build
validation require separate review criteria.

## Observed Friction

- On Windows, the checked-out `scripts/smoke-antennapod.sh` failed under default
  WSL Bash because of CRLF line endings.
- The default `bash` available in PowerShell was WSL Bash and did not have
  `python` installed; Git for Windows Bash was needed for the helper.
- The helper's repository-root detection depends on the helper being run from
  the repository's `scripts/` directory. A copied helper outside the repository
  computes the wrong root.
- `localize-run` writes `.localize-anything/` project state inside the target
  checkout even when generated outputs are directed outside the project. This is
  acceptable for a disposable clone but should be clear in smoke-test docs.
- Evidence paths are verbose on Windows and not summarized into one compact
  smoke-test report by the runtime.
- Review and risk artifacts exist, but discovering the most relevant summary
  files still requires inspecting the run-summary artifact map.

## Follow-up Candidates

- Make the smoke-test helper line-ending robust on Windows.
- Clarify in the smoke-test guide that Git for Windows Bash is preferred on
  Windows when WSL does not have the project Python environment.
- Add a compact non-destructive smoke-test summary artifact.
- Make `localize-run` output-directory and `.localize-anything/` state behavior
  more explicit in CLI help.
- Improve review-sheet and delivery-decision discoverability from the command
  output.

## Conclusion

The smoke test passed for read-only inspection, synthetic blind generation,
staging, deterministic QA, review artifact creation, and delivery evidence
collection against a disposable AntennaPod clone.

Tracked AntennaPod source files were not modified. The only target-checkout
mutation observed was expected untracked `.localize-anything/` local project
state, which was removed after the test. A destructive apply step and production
translation generation were intentionally not executed.
