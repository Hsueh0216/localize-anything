# AntennaPod DeepSeek Localization Test — 2026-06-20

## Summary

First real LLM translation test with `deepseek-chat` model.
AntennaPod Android strings (869 segments) → Japanese + Korean.
Full pipeline: extract → batch → DeepSeek API → collect → stage → QA → deliver.

## Results

| Metric | Japanese (ja) | Korean (ko) |
|--------|--------------|-------------|
| Source | `ui/i18n/src/main/res/values/strings.xml` | same |
| Commit | `85c2993b6fb1a48dcb81327bd9841fd7c7d668e2` | same |
| Segments | 869 | 869 |
| Batches | 29 (30/batch) | 29 (30/batch) |
| API Model | `deepseek-chat` | `deepseek-chat` |
| Duration | ~4 min | ~4 min |
| Collection | pass | pass |
| QA | pass (0 blocking, 0 warnings) | pass (0 blocking, 0 warnings) |
| Staged Output | `deepseek-ja/staging/res/values-ja/strings.xml` | `deepseek-ko/staging/res/values-ko/strings.xml` |

## Translation Quality Samples

```
EN: "Expand"                    JA: "展開"                    KO: "펼치기"
EN: "Collapse"                  JA: "折りたたむ"               KO: "접기"
EN: "Add podcast"               JA: "ポッドキャストを追加"      KO: "팟캐스트 추가"
EN: "Settings"                  JA: "設定"                    KO: "설정"
EN: "Queue"                     JA: "キュー"                  KO: "대기열"
EN: "Playback speed"            JA: "再生速度"                 KO: "재생 속도"
EN: "Want to join? Whether..."  JA: "参加してみませんか？翻訳..."  KO: "참여하고 싶으신가요? 번역..."
EN: "Phone not compatible..."   JA: "電話が互換性がありません..."  KO: "휴대폰이 호환되지 않습니다..."
```

All 869 segments × 2 languages produced real translations — zero fallback markers.

## Pipeline Reproduction

```bash
cd test02-antennapod
python run_deepseek.py
```

Or using the CLI:

```bash
# Extract
localize-anything extract-android-strings source/res/values/strings.xml \
  --source-locale en-US --output segments.jsonl

# Generate with DeepSeek
localize-anything deepseek-generate segments.jsonl \
  --target-locale ja --generated-output generated-ja.jsonl

# Stage
localize-anything stage-android-strings source/res/values/strings.xml \
  generated-ja.jsonl --target-locale ja --staging-dir staging --project-root source
```

## Bugs Found & Fixed

| # | Severity | Bug | Location | Fix |
|---|----------|-----|----------|-----|
| P0 | Blocking | `%% of` in source parsed as `% o` placeholder | `json_adapter.py:17` | Fixed regex: `r"|%\\%"` → `r"|%%"`, filter `%%` from results |
| P1 | Blocking | DeepSeek hallucinated extra `%2$s` placeholder in 1 KO segment | `deepseek_provider.py` | Added `_fix_placeholder_parity()` auto-strip |
| P2 | Crash | Collection failure returned inconsistent dict, crashed summary print | `run_deepseek.py` | Consistent result shape with `.get()` fallbacks |

## DeepSeek Provider Module

`runtime/localize_anything/deepseek_provider.py`

- API: `translate_batch_deepseek(segments, target_locale)`
- CLI: `localize-anything deepseek-generate`
- Auto placeholder parity validation
- Key auto-discovery: `DEEPSEEK_API_KEY` env → `~/.deepseek/api_key` → `.env.reasonix`
- Temperature 0.1, max_tokens 8192

## Limitations

- Machine translation quality; human review recommended for production use
- 2 segments (batch-0029) previously required manual placeholder fix — now automated
- Non-Android formats (iOS .strings, XLIFF, gettext) not yet tested with DeepSeek
- Dictionary-based baseline test also available in `run_localize.py` (59 manual entries/lang)
