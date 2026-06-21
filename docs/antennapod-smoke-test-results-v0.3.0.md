# AntennaPod Smoke Test Results for v0.3.0

## Summary

This was a disposable-clone smoke test against AntennaPod for v0.3.0
pre-release evidence. AntennaPod was cloned outside this repository and was not
vendored.

Generated outputs, delivery packages, review sheets, run directories, and
temporary evidence files were kept outside this repository and were not
committed. The test focused on workflow safety, inspect-summary evidence,
source mutation checks, and synthetic draft pipeline behavior. It did not
evaluate translation quality.

No destructive apply step was run. Provider-backed translation was not run.

## Relationship To v0.2.x Evidence

The historical v0.2.x smoke-test results remain in
`docs/antennapod-smoke-test-results.md`. This document records a new v0.3.0
pre-release run after the inspect-summary and workflow-safety hardening work.

The v0.3.0 run adds compact `inspect-summary.json` and `inspect-summary.md`
evidence and confirms the updated smoke-test helper output. It does not claim
full production localization of AntennaPod.

## Environment

- Date: 2026-06-21
- OS / shell: Windows PowerShell, with Git for Windows Bash for the shell helper
- Localize Anything commit: `306f34c7cf3f47acdcd5dfb51924922d6d9d8d07`
- Localize Anything package version: `0.2.5`
- Localize Anything protocol version: `0.1`
- AntennaPod commit: `f7f0314888631208fedb26518fd924cb7805062f`
- AntennaPod clone location policy: temporary directory outside this repository
- Evidence output policy: temporary directory outside this repository and outside
  the AntennaPod clone

## Commands Run

The smoke-test helper was run against the disposable AntennaPod clone:

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts/smoke-antennapod.sh `
  "$tmpRoot/AntennaPod" `
  "$tmpRoot/evidence/helper"
```

The helper ran these non-destructive checks:

```bash
git -C "$tmpRoot/AntennaPod" rev-parse HEAD
git -C "$LOCALIZE_ANYTHING_REPO" rev-parse HEAD
python -m runtime.localize_anything inspect --project "$tmpRoot/AntennaPod" --output "$tmpRoot/evidence/helper/inspection.json"
python -m runtime.localize_anything inspect --project "$tmpRoot/AntennaPod" --output-dir "$tmpRoot/evidence/helper/inspect-summary" --output "$tmpRoot/evidence/helper/inspect-summary.json"
python -m runtime.localize_anything validate-protocol
python -m runtime.localize_anything validate-contracts
```

The scoped synthetic blind workflow was then run against the Android source
resource used by the earlier v0.2.x evidence:

```powershell
python -m runtime.localize_anything localize-run "$tmpRoot/AntennaPod" `
  --source-locale en-US `
  --target-locale zh-CN `
  --source-file ui/i18n/src/main/res/values/strings.xml `
  --output-root "$tmpRoot/evidence/runs" `
  --run-id antennapod-v030-blind-smoke `
  --synthetic-draft `
  --operating-mode blind_benchmark `
  --reference-policy blind `
  --workflow-depth standard `
  --output "$tmpRoot/evidence/run-summary.json"
```

Source mutation checks:

```bash
git -C "$tmpRoot/AntennaPod" status --short
git -C "$tmpRoot/AntennaPod" diff --exit-code
```

## Results

- Helper result: passed.
- Inspect summary result: passed.
- Available inspect artifacts:
  - `inspection.json`
  - `inspect-summary/inspect-summary.json`
  - `inspect-summary/inspect-summary.md`
- Inspect summary detected project type: `mixed`
- Primary adapter: `core.android-strings`
- Supported files detected: 125
- Android resource files detected: 53
- Android source sets detected: `main`
- Existing Android target-locale references detected: 52
- Android resource type counts observed:
  - `string`: 31314
  - `string-array`: 0
  - `plurals`: 1133
- Inspect summary read-only flag: `true`
- Synthetic blind `localize-run` result: `draft_package_created`
- Source file used for synthetic workflow:
  `ui/i18n/src/main/res/values/strings.xml`
- Segments extracted: 869
- Candidate segments: 869
- Preserved segments: 0
- Batch count: 11
- Output count: 1
- Generation mode: `synthetic_draft`
- Operating mode: `blind_benchmark`
- Reference policy: `blind`
- QA status: `pass_with_warnings`
- QA warnings: 2
- Review, delivery decision, delivery dashboard, and apply-plan artifacts were
  created in the temporary evidence directory.
- Risk metadata appeared in generated/work-packet artifacts.

The apply plan was generated as a non-mutating planning artifact. `apply-delivery`
was not executed.

## Source Mutation Check

Before helper:

```text
# no output
```

After helper:

```text
# no output
```

After synthetic `localize-run`, expected Localize Anything project state appeared
inside the disposable AntennaPod clone:

```text
?? .localize-anything/
```

Tracked source files were not modified:

```text
git -C "$tmpRoot/AntennaPod" diff --exit-code
# exit 0
```

The temporary `.localize-anything/` state was removed after recording the
summary, and the disposable clone returned to a clean status:

```text
# no output
```

## Not Executed

- Provider-backed translation was not executed.
- Production translation generation was not executed.
- `apply-delivery` was not executed.
- Destructive apply was not executed.
- AntennaPod build, Gradle validation, APK validation, and device testing were
  not executed.
- Unrestricted mixed-project `localize-run` was not used as evidence. A prior
  attempted unrestricted run selected an unsupported CSV source in the mixed
  AntennaPod checkout, so this evidence uses the documented Android source-file
  scope.

## Observed Friction

- Real-project inspection can detect a mixed project even when Android resources
  are the primary target. Source-file scoping remains important for synthetic
  Android smoke tests.
- `localize-run` creates `.localize-anything/` state inside the target checkout.
  This remains acceptable only for disposable clones unless the project owner
  approves the state directory.
- The run creates review and delivery artifacts, but users still need to inspect
  the run summary to find the most relevant files.
- This run confirmed that the shell helper now emits compact inspect-summary
  artifact paths and that shell syntax is LF-normalized.

## Follow-up Candidates

- Improve source-file selection guidance for mixed real projects.
- Make artifact path summaries more compact in `localize-run` output.
- Make `.localize-anything/` state creation more visible before running
  `localize-run` on non-disposable projects.
- Add a non-destructive source-selection preview for mixed projects if needed.

## Conclusion

The v0.3.0 pre-release smoke test passed for read-only inspection,
inspect-summary evidence, scoped synthetic blind generation, staging,
deterministic QA, review artifact creation, and delivery evidence collection
against a disposable AntennaPod clone.

The run did not validate provider-backed translation, translation quality,
destructive apply, AntennaPod build correctness, layouts, drawables, assets,
Gradle editing, APK decompilation, or full production localization.
