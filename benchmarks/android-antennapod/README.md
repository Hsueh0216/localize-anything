# AntennaPod Android Strings Benchmark

This benchmark exercises the v0.2 Android source-project slice against
AntennaPod, a well-known open-source Android podcast client. It validates that
Localize Anything can produce a staged drop-in language resource for a real
project layout without repackaging an APK or editing source code in place.

The benchmark downloads only the pinned upstream
`ui/i18n/src/main/res/values/strings.xml` file. It does not commit or vendor
AntennaPod source files.

Run:

```bash
python3 benchmarks/android-antennapod/run.py \
  benchmarks/android-antennapod/work/latest
```

To run the full Android app-copy E2E flow through the shared agent runtime:

```bash
python3 -m runtime.localize_anything android-app-test \
  benchmarks/android-antennapod/work/latest/source \
  --source-locale en-US \
  --target-locale zh-CN \
  --output-root benchmarks/android-antennapod/work/android-app-e2e \
  --run-id android-app-e2e-synthetic-001 \
  --max-segments 20
```

This copies the pinned source workspace, applies the staged
`values-zh-rCN/strings.xml` only to the copy, validates Android resources after
apply, and records source-preservation evidence in
`android-app-test-report.json`.

To run the same app-copy E2E path with local generated Chinese draft JSONL
instead of the synthetic prefix draft:

```bash
python3 -m runtime.localize_anything android-app-test \
  benchmarks/android-antennapod/work/latest/source \
  --source-locale en-US \
  --target-locale zh-CN \
  --local-chinese-draft \
  --require-real-generation \
  --output-root benchmarks/android-antennapod/work/android-app-e2e \
  --run-id android-app-e2e-local-auto-001 \
  --max-segments 20
```

The latest single-command local generated-input run passed with
`provider: codex-local`, `quality_claim: local_chinese_draft_for_e2e`, 869
generated segments, 44 batches, one copied `values-zh-rCN/strings.xml`, source
preservation, and post-apply Android QA `pass` with zero warnings.

To hand work to a host agent instead of using the synthetic verification draft:

```bash
python3 benchmarks/android-antennapod/run.py \
  benchmarks/android-antennapod/work/latest \
  --handoff-only
```

The host agent reads `evidence/generation-handoff.json`, writes each generated
batch to the listed JSONL path, then reruns the benchmark with `--keep-existing`
and `--generated-dir <dir>`.

The default run builds provider-agnostic draft requests for each work packet,
then uses a synthetic target draft that preserves source text and placeholders
with a target-locale prefix. That synthetic draft is only evidence for draft
contract validation, adapter staging, QA, packaging, and dashboard behavior. It
is not translation-quality evidence.

The pinned source currently extracts 869 segments into 44 default batches and
should finish with Android QA status `pass` and zero warnings.

Expected generated target path:

```text
ui/i18n/src/main/res/values-zh-rCN/strings.xml
```

## Verification Focus

- Detect the Android strings adapter on a real project path.
- Extract Android `<string>`, `<string-array>`, and `<plurals>` resources into
  protocol segments.
- Create host-agent draft requests from work packets.
- Validate generated segment JSONL before staging output files.
- Keep `translatable="false"` resources out of the generated target, with QA
  evidence for skipped resources.
- Stage the target locale file instead of mutating the source workspace.
- Produce a delivery snapshot, developer/translator dashboard, and Delivery
  Agent decision report.

## Licensing

The benchmark runner and metadata use this repository's MIT license. Downloaded
AntennaPod source files retain their upstream GPL-3.0 license and remain in the
ignored benchmark work directory.
