# Localize Anything Protocol 0.1

## Purpose

Define portable artifacts between agents, runtimes, and adapters. The protocol does not prescribe a model provider or implementation language.

## Canonical Artifacts

- Project configuration selects operational policy.
- Project sessions record source-selection policy, routing decisions, resumable
  run state, and links to prior run directories for CLI/Web UI continuation.
- Adapter manifests declare formats, capabilities, permissions, dependencies, and entrypoints.
- Segment JSONL carries source units and optional localized targets.
- Delivery manifests record immutable run facts and scoped status.
- Term decisions record approved, locked, rejected, risky, or scoped
  terminology decisions with provenance. `term-decisions.jsonl` stores one
  `term-decision` record per line; `term-registry.csv` and
  `forbidden-translations.csv` provide deterministic runtime inputs for hard
  terminology constraints.
- Delivery decision reports combine QA findings, staged output state, apply
  plans, and unprocessed assets into explicit owner/developer decisions.
- QA results keep runtime, agent, and human evidence distinct.
- LLM review requests and results keep model-based translation critique as
  segment-level issues, separate from deterministic QA and human acceptance.
- Batch plans group segments by content unit and adapter constraints.
- Work packets carry an ephemeral, budgeted context selection.
- Work packets may include `memory.hard_constraints` for approved or locked
  term-registry entries, forbidden translations, structural rules, and future
  claim constraints. Blind benchmark mode hides target-language term registry
  and translation-memory content from generation-facing packets.
- Draft requests turn a work packet into provider-agnostic host-agent
  instructions and a JSONL segment output contract for translation generation.
- Draft prompts render those requests as paste-ready Markdown for manual
  host-agent LLM workflows.
- Generated response imports normalize single-batch or handoff-wide LLM
  response shapes into canonical generated segment JSONL using work-packet
  source fields as the authority.
- Generation handoff manifests coordinate multi-batch draft requests and
  expected generated JSONL paths for host-agent execution.
- Staging manifests record adapter-routed output files created from generated
  segments before packaging or applying anything to the source project.
- Run summaries record orchestration-level artifact paths and next actions for
  developer-facing command runs.
- Agent summaries separate Project, Generation, Review, and Delivery decisions
  so direct-provider, handoff, CLI, and Web UI workflows can be audited through
  the same protocol artifacts.
- Android app test reports prove an isolated source-project copy can be routed,
  localized, applied, and revalidated without mutating the original project.
- Incremental diffs classify new, unchanged, changed, moved, and deleted segments.
- Acceptance records bind scoped sign-off to an immutable manifest hash.
- Apply plans describe dry-run operations without mutating the project.

## Lifecycle

```text
inspect -> preflight -> plan -> retrieve -> draft-request -> draft-prompt
        -> generation-handoff -> localize -> import-generated-response(s)
        -> collect-generated
        -> stage-generated -> validate-output -> package
        -> delivery-decision -> review-import -> sign-off -> apply
```

`localize-run` is a reference-runtime convenience command for this lifecycle.
It emits provider-agnostic draft requests for host-agent translation generation,
then, once generated segment JSONL is supplied, writes staged target files,
packages them, and produces a dashboard. It does not make model-provider calls
or overwrite source project files.
`agent-run` is the first agent shell over the same lifecycle. It records the
routing decision, exposes parallel translation batches to direct-provider or
host LLM workflows, imports returned responses when available, and reflects
through deterministic QA, optional LLM critique, review sheets, dashboard,
delivery-decision, and apply-plan artifacts. It uses the same generated segment
JSONL contract for direct provider execution and handoff/import fallback, and
does not overwrite source project files.

Adapters implement the narrower lifecycle documented in `docs/adapters.md`.

## Localization Modes

`operating_mode` and `reference_policy` are first-class protocol fields on
project config, batch plans, work packets, draft requests, delivery manifests,
project sessions, and agent summaries.

Supported `operating_mode` values:

- `blind_benchmark`: generate without target-locale reference text.
- `greenfield_localization`: create a new locale from source material.
- `existing_locale_maintenance`: update an existing locale while preserving
  reviewed unchanged translations.
- `rewrite_or_harmonization`: intentionally revise or harmonize existing
  translations.

Supported `reference_policy` values:

- `blind`: no glossary target terms or translation memory target text may be
  exposed to generation packets.
- `style_only`: approved terminology and style guidance may be exposed, but
  existing target segment translations are excluded.
- `tm_assisted`: approved translation memory may be exposed as generation
  context.
- `preserve_existing`: reviewed unchanged translations are preserved outside
  generation, and only unresolved segments become generation candidates.

Default mode is `greenfield_localization` with `style_only`. Blind benchmarks
must use `blind`; existing-locale maintenance cannot use `blind`.

## Delivery Status

- `draft_package`
- `review_ready`
- `blocked`
- `applied_draft`
- `user_accepted`

Only an explicit user action can produce `user_accepted`.

## Compatibility

All protocol documents carry `protocol_version`. A runtime must reject unsupported major versions and may accept additive minor-version fields when its schema permits them.
