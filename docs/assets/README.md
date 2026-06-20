# docs/assets/

Asset inventory for the Localize Anything documentation.

## Current state

This directory currently contains no SVG/PNG assets.

Diagrams in README.md and README.zh-CN.md use **Mermaid**
(rendered by GitHub and most Markdown viewers), so no generated
SVG files are needed.

## Planned assets

| File | Purpose | Status |
|------|---------|--------|
| `workflow-dark.svg` | Main localization workflow diagram | Not yet created |
| `architecture-layers.svg` | Protocol → Runtime → Agent → Adapter layers | Not yet created |
| `delivery-package.svg` | Delivery package structure | Not yet created |
| `benchmark-antennapod.svg` | AntennaPod benchmark results visualization | Not yet created |

## Conventions

- All assets should be editable by hand or via a documented toolchain
- Prefer SVG over PNG for diagrams
- Auto-generated assets (e.g., benchmark charts) should include their generation script path
- Do not commit large (> 1 MB) binary assets without explicit review
