# Localize Anything Roadmap — Optimized v0.2 Development Path

## v0.1-alpha: Vertical Slice

Status: implemented.

Purpose: prove the full localization protocol and workflow on controlled text localization tasks.

Completed scope:

* protocol schemas and examples
* lightweight reference CLI
* four-layer memory initialization
* preflight inventory and batch planning contracts
* stable segment IDs and source hashes
* staged rebuild and deterministic QA
* immutable delivery package
* incremental update detection
* review import and scoped sign-off
* apply dry-run
* The South Guard blind-generation benchmark definition

## v0.1-beta: Common Text Formats

Status: implemented.

Purpose: prove adapter-based extraction, rebuild, and deterministic QA across common text-like formats.

Completed scope:

* YAML/TOML
* CSV/TSV/XLSX
* Markdown/HTML
* SRT/VTT
* XLIFF
* fixture-based extraction and rebuild coverage
* documented adapter capability levels and limitations

---

# v0.2: Platform Enablement and Reliable Agent Localization

## v0.2 Goal

v0.2 turns Localize Anything from a working localization automation framework into a reliable agent-assisted localization system for real source projects.

The focus is not more formats. The focus is trustworthy project localization for Android/iOS source projects and small developer products.

v0.2 should prove that the framework can:

* safely localize real source projects;
* preserve platform resource structure;
* support both new-product localization and existing-locale maintenance;
* use project memory without blindly copying reference translations;
* detect high-risk translation, structure, and delivery problems;
* produce review-ready deliverables that developers can trust before applying.

## v0.2 Non-Goals

* APK/IPA repackaging.
* Broad game engine support.
* Large document workflows.
* Community adapter marketplace.
* Full visual localization.
* Native-level quality claims without qualified human review.
* Automatic overwrite of source projects.

---

# v0.2.0: Agent Runtime Baseline

Status: mostly implemented.

Purpose: establish the agent architecture and artifact-based workflow foundation.

Completed or baseline scope:

* split runtime responsibilities into Project, Generation, Review, and Delivery agent responsibilities;
* project/session state and artifact-first session index;
* routing evidence and agent-summary artifacts;
* generated run folders and source-selection ignore rules;
* retry-handoff failed-batch recovery;
* direct provider execution through generated-segment JSONL;
* provider-agnostic handoff/import fallback;
* LLM review request and review import artifacts;
* delivery-decision artifacts;
* staged apply operations;
* non-mutating apply plans;
* backup and rollback metadata;
* localhost-only Web Workbench baseline;
* Android app E2E proof;
* real-generated Android fixture proof;
* AntennaPod local generated-input Android proof.

Exit criteria:

* A developer can run a real project through preflight, generation, review, staging, delivery dashboard, and apply plan without mutating the original project.
* Failed generation batches can be inspected, retried, and re-collected.
* Delivery decisions are visible as protocol artifacts.

---

# v0.2.1: Localization Mode System

Purpose: prevent the system from treating benchmark generation, new-product localization, and existing-locale maintenance as the same task.

## Add Reference Policy

Introduce `reference_policy` as a first-class protocol field.

Supported policies:

* `blind`

  * Existing target translations are hidden from generation.
  * Used for benchmarks and model/system evaluation.

* `style_only`

  * Existing references are analyzed only for terminology, style, and conventions.
  * Direct segment-level copying is not allowed.
  * Used when the user wants inspiration but not inheritance.

* `tm_assisted`

  * Existing translations may provide scoped TM suggestions and glossary candidates.
  * Generation remains grounded in the confirmed source.
  * Used for ongoing localization work.

* `preserve_existing`

  * Existing target translations are preserved by default when source hashes are unchanged.
  * Missing, stale, or explicitly selected segments receive generated candidates.
  * Used for mature projects with existing locale files.

## Add Operating Modes

Supported project modes:

* `blind_benchmark`
* `greenfield_localization`
* `existing_locale_maintenance`
* `rewrite_or_harmonization`

## Required Behavior

For `greenfield_localization`:

* build memory from source project, product description, user preferences, and reviewed generated outputs;
* do not assume an existing target locale;
* use glossary and translation memory only after user review or scoped acceptance.

For `existing_locale_maintenance`:

* use the original source as source truth;
* treat existing target files as reference evidence, not source truth;
* preserve unchanged reviewed translations by default;
* generate candidates only for missing, stale, conflicting, or user-selected segments;
* flag obsolete target segments without deleting them automatically.

For `blind_benchmark`:

* hide existing target translations from Generation Agent;
* allow target references only in evaluation artifacts;
* clearly label benchmark claims.

Exit criteria (all met — June 2026):

* The same project can be run in blind benchmark mode or maintenance mode with visibly different behavior.
* Existing locale files no longer cause mass rewrites unless the user explicitly selects rewrite mode.
* Benchmark runs cannot accidentally leak reference translations into generation packets.
* **Verified**: Obsolete target-only keys are detected, preserved in staged output, and not silently deleted.
* **Verified**: Negative tests confirm blind leakage, maintenance mass rewrite, and obsolete key dropping are all rejected.
* Full evidence: `benchmarks/v021-mode-system/report.json`, `docs/v0.2.1-verification.md`.

Status: **verified** 🗹

---

# v0.2.2: Android Resource Reliability

Purpose: upgrade Android support from XML round-trip to platform-aware localization.

## Android Adapter Improvements

Support and preserve:

* `string`
* `string-array`
* `plurals`
* `translatable="false"`
* product flavors and source-set variants when detectable
* resource comments when useful for context
* XML entities
* escaped apostrophes and quotes
* `\n`, `\t`, and other escaped control sequences
* Android formatting placeholders such as `%1$s`, `%2$d`, `%1$d%%`
* inline HTML tags
* CDATA blocks
* resource ordering where practical

## Protected Span System

Each extracted segment should include:

* `segment_id`
* `resource_name`
* `resource_type`
* `source_text`
* `existing_target_text`
* `translatable_text`
* `protected_spans`
* `placeholder_signature`
* `markup_signature`
* `escape_signature`
* `source_hash`
* `target_hash`
* `resource_context`

The Generation Agent may only modify translatable text. Protected spans must survive generation, normalization, staging, and rebuild.

## Android Context Classification

Classify strings into UI roles when possible:

* button
* menu item
* setting title
* setting summary
* dialog title
* dialog message
* destructive confirmation
* error message
* notification channel
* TalkBack/accessibility text
* empty state
* statistics text
* marketing or onboarding copy

Exit criteria:

* Android generated files pass deterministic validation after staging and after apply-to-copy.
* CDATA, inline HTML, placeholders, and escaped sequences survive round-trip.
* High-risk Android strings are clearly marked in review artifacts.
* AntennaPod can run without structure-loss findings in staged Android QA.

---

# v0.2.3: Project Memory and Terminology Pipeline

Purpose: make the four-layer memory operational instead of only structural.

## Memory Initialization

During preflight, create or update:

* `localization-context.md`
* `glossary.csv`
* `translation-memory.jsonl`
* `delivery-manifest.json`
* `qa-report.md`

## Automatic Glossary Candidate Extraction

Extract candidates from:

* source resource names;
* repeated source phrases;
* existing target locale files;
* app name and brand strings;
* README or app metadata if available;
* user-provided terminology;
* reviewed human edits.

Each glossary entry should include:

* source term
* approved target term
* forbidden alternatives
* locale
* scope
* confidence
* provenance
* review state

## Translation Memory Rules

TM entries must include:

* source segment
* target segment
* source hash
* locale
* review state
* provenance
* scope
* last accepted run
* whether it is generated, reviewed, or imported

Do not globally promote generated text without scoped acceptance.

## Reference Firewall

Project Agent may inspect existing target files.

Generation Agent receives only:

* relevant glossary entries;
* approved TM snippets;
* style guidance;
* protected-span rules;
* current source batch;
* necessary neighboring context.

Review Agent may compare generated candidates against existing translations and explain whether to keep, replace, or ask for human review.

Exit criteria:

* Existing translations improve terminology consistency without becoming hidden source truth.
* Greenfield projects build useful memory over repeated runs.
* Human review edits can be imported and promoted with scoped rules.
* Re-running a project shows fewer inconsistent term choices.

---

# v0.2.4: Semantic Review Agent

Purpose: move LLM review from general linguistic reflection to actionable localization risk detection.

## Review Categories

The Review Agent should check:

* omission
* mistranslation
* hallucinated meaning
* action changed
* condition changed
* negation changed
* consequence softened
* warning weakened
* number/date/time/range changed
* placeholder misuse
* markup misuse
* terminology drift
* tone mismatch
* UI length risk
* locale-specific unnaturalness
* cultural or market adaptation concern

## Severity Levels

Use severity levels:

* `blocker`
* `high`
* `medium`
* `low`
* `info`

## Confidence Levels

Use confidence levels:

* `high`
* `medium`
* `low`

## High-Risk String Classes

Automatically elevate review priority for:

* delete, remove, clear, reset
* import, export, restore, backup
* login, authentication, password
* sync and account linking
* mobile data, VPN, network cost
* automatic download
* queue behavior
* storage and file deletion
* permissions
* security and privacy
* irreversible actions

## Repair Loop

For failed or high-risk segments:

1. identify issue;
2. generate targeted repair request;
3. repair only affected segments;
4. re-run deterministic QA;
5. re-run semantic review if needed;
6. update QA evidence.

Exit criteria:

* The system can detect meaning-loss cases such as missing disable/auto-download behavior.
* Review output is segment-level and actionable.
* Repair does not rewrite entire batches without cause.
* QA report separates deterministic failures from linguistic/cultural findings.

---

# v0.2.5: Risk-Based Dashboard and Review Workflow

Purpose: make review usable for developers and small teams.

## Dashboard Sections

The delivery dashboard should show:

* run summary
* target locales
* source files
* generated files
* delivery state
* apply plan
* coverage
* new segments
* preserved segments
* stale segments
* obsolete segments
* conflicts
* deterministic QA results
* LLM review results
* unprocessed assets
* required user decisions
* next recommended action

## Risk Queues

Group review items as:

* P0: structure or build risk
* P1: user-harm or product-behavior risk
* P2: terminology and consistency risk
* P3: style and polish
* New: generated missing translations
* Obsolete: target exists but source missing
* Preserved: unchanged existing translation
* Blocked: requires user input

## Review Sheet Improvements

Export review sheets in Markdown and CSV with:

* key
* source
* existing target
* generated target
* proposed action
* risk level
* issue category
* evidence
* reviewer note
* user decision
* final accepted target

## Decision Actions

Allow per-segment decisions:

* accept generated
* keep existing
* edit manually
* mark needs translator review
* defer
* reject
* add glossary entry
* add forbidden term
* promote to TM

Exit criteria:

* A developer can review high-risk items first instead of reading hundreds of diffs.
* Review decisions can be imported back into project memory.
* The dashboard recommends the next action clearly.
* Apply is blocked when P0 findings remain unresolved.

---

# v0.2.6: iOS and String Catalog Reliability

Purpose: bring iOS/macOS support to the same reliability level as Android.

## iOS Resource Support

Support:

* `.strings`
* `.stringsdict`
* `.xcstrings`

Preserve:

* keys
* comments
* format placeholders
* plural rules
* device/platform variations when available
* String Catalog metadata
* staged updates without source mutation

## iOS QA

Validate:

* placeholder compatibility;
* plural category coverage;
* JSON structure for `.xcstrings`;
* source-target key alignment;
* staged rebuild integrity;
* apply-to-copy safety.

## Benchmarks

Use:

* Signal-iOS `.strings`
* IceCubesApp `.xcstrings`

Exit criteria:

* iOS resources can be staged and validated without corrupting project files.
* `.xcstrings` updates remain reviewable and reversible.
* iOS benchmark runs produce delivery-decision artifacts comparable to Android.

---

# v0.2.7: Pseudo-Localization and Layout Risk Signals

Purpose: add lightweight layout and UI risk detection without overbuilding visual QA.

## Pseudo-Localization

Add optional pseudo-localization for:

* length expansion;
* accent marks;
* bracketed strings;
* placeholder preservation;
* RTL simulation where applicable.

Pseudo-localization must not pollute glossary, TM, or context memory.

## Layout Risk Signals

Detect:

* unusually long translations;
* short source strings with much longer targets;
* button-like strings exceeding practical length;
* settings titles likely too long;
* dialog messages with excessive expansion;
* missing translations that fall back to source language.

## Conditional Visual QA

Where practical, expose hooks for:

* Android screenshot tests;
* iOS simulator screenshots;
* developer-provided screenshots;
* manual visual QA attachment.

If visual QA is not run, record `visual_qa_not_run`.

Exit criteria:

* Pseudo-localization can run as a separate non-persistent QA mode.
* Layout risk appears in dashboard.
* The system does not claim visual safety unless visual QA actually ran.

---

# v0.2.8: Web Workbench Review Experience

Purpose: make the artifact workflow usable by non-specialist developers.

## Workbench Features

Add:

* session list and resume;
* run timeline;
* source inventory view;
* locale status view;
* batch status view;
* side-by-side segment review;
* risk queue filters;
* glossary editor;
* TM review/promote view;
* QA report viewer;
* apply-plan viewer;
* run-id confirmation for apply;
* download delivery package.

## Localhost-Only Constraint

Workbench remains localhost-only for v0.2.

No hosted service, accounts, cloud storage, or remote project upload is required.

Exit criteria:

* A small developer can complete a greenfield localization review without editing raw JSONL.
* A maintainer can review existing-locale updates by risk level.
* CLI and Web UI operate over the same protocol artifacts.

---

# v0.2.9: Real-World Benchmark and Release Candidate

Purpose: prove v0.2 reliability on realistic open-source projects.

## Benchmark Matrix

Run controlled and real-world tests on:

* AntennaPod Android resources
* Signal-iOS `.strings`
* IceCubesApp `.xcstrings`

For each benchmark, record:

* project commit
* source locale
* target locale
* mode
* reference policy
* model/provider
* workflow depth
* adapter versions
* number of segments
* generated segments
* preserved segments
* repaired segments
* deterministic QA findings
* semantic review findings
* human review status
* apply plan status
* whether source project was mutated

## Evidence Levels

Report results with evidence levels:

* E0: deterministic structural validation
* E1: automated linguistic review
* E2: bilingual human spot check
* E3: native speaker review
* E4: professional localization review

Do not claim higher quality than the available evidence supports.

## Release Candidate Criteria

v0.2 can be considered release-ready when:

* Android and iOS project runs can complete without source mutation;
* apply-to-copy validation passes;
* protected spans survive round-trip;
* maintenance mode preserves unchanged existing translations;
* greenfield mode builds useful memory across reruns;
* review dashboards prioritize actionable risks;
* P0 findings block apply;
* benchmark reports are reproducible;
* documentation explains modes, reference policy, QA evidence, and limitations.

---

# Later Releases

## v0.3: Game and Web Enablement

Add:

* generic game localization enablement;
* Unity;
* Godot;
* Unreal;
* Ren'Py;
* web framework overlays;
* route/page/component-level localization guidance.

## v0.4: Document and Presentation Workflows

Add:

* DOCX;
* PPTX;
* PDF inspection workflow;
* structured document review;
* layout-aware document QA where possible.

## v0.5: Multimodal Localization

Add:

* image text inventory;
* image translation planning;
* audio/subtitle coordination;
* voice/script localization workflow;
* asset-level QA records.

## v0.6: MCP and Community Adapter Ecosystem

Add only after the core adapter contract and security model are stable:

* MCP integrations;
* governed adapter registry;
* explicit adapter installation;
* version locking;
* checksums;
* trust tiers;
* permissions;
* fixtures;
* contract tests;
* project-local private adapters.
