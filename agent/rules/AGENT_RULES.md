# Agent Rules Index

This directory contains YAML configuration files mapping linter rule IDs to their corresponding fixer implementation class, skill prompt, safety tier, and batch eligibility.

## Safety Tiers
- **safe**: Fully deterministic insertion/format fix — eligible for `--batch`.
- **interactive**: Requires human choice/review — skipped in `--batch` unless confirmed.
- **unsafe**: Report-only in CLI mode — no auto-fixer.
