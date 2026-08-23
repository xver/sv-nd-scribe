# SV ND Scribe AI Agent — Phase 1 (MVP) Dev Checklist

This checklist is the authoritative task tracker for completing Phase 1 (MVP) of the SV ND Scribe AI Agent.

---

## 1. Core Modules
- [x] `agent/agent.py`: Implement `ScribeAgent` with deterministic pipeline (no overrides, no auto-detect).
- [x] `agent/__main__.py`: CLI entry point with `-f`, `--interactive`, `--batch`, `--dry-run`, `--rules`, `--llm`, `--status`.
- [x] `agent/fixer/base_fixer.py`: Define `FixProposal` dataclass + `BaseFixer` abstract interface.
- [x] `agent/fixer/file_fixer.py`: Atomic file I/O + backup strategy (`auto` / `always` / `never`).

---

## 2. Fixers (Safe Rules Only)
Implement all Phase 1 Required Fixers:
- [x] `fix_wkl005_eof_newline.py` (WKL-005)
- [x] `fix_wkl006_trailing_whitespace.py` (WKL-006)
- [x] `fix_wkl008_no_tabs.py` (WKL-008)
- [x] `fix_nd001_file_header.py` (ND-001 simple header mode with `TODO_*` placeholders)
- [x] `fix_nd002_include_guard.py` through `fix_nd011_type_doc.py` (ND-002..ND-011)
- [x] `fix_nd013_interface_doc.py` through `fix_nd018_checker_kind.py` (ND-013..ND-018)
- [x] `fix_nd020_constraint_doc.py` through `fix_nd022_coverpoint_doc.py` (ND-020..ND-022)
- [x] `fix_nd025_checker_doc.py` through `fix_nd026_bind_doc.py` (ND-025..ND-026)
- [x] `fix_nd028_assign_doc.py` through `fix_nd032_modport_doc.py` (ND-028..ND-032)

---

## 3. LLM Abstraction Layer
- [x] `agent/llm/none_provider.py`: Implement default deterministic provider.
- [x] Implement active LLM provider (`openai_provider.py` or `ollama_provider.py`) with `llm_timeout_sec` and explicit fallback to `none`.

---

## 4. VS Code Extension Integration
- [x] Add deterministic quick-fix `CodeAction` that runs `python3 -m agent --llm none --json --dry-run` and applies `patch_lines`.
- [x] Add optional AI `CodeAction` that runs `--llm <provider>`, shows diff preview, and applies only on user confirm. (Do not offer if `agentLlmProvider == "none"`).

---

## 5. Tests & CI
- [x] Test deterministic dry-run and batch fix on `makedir/test_bad_sv.f`.
- [x] Re-lint after batch fix; assert no new syntax errors and zero remaining Safe violations.
- [x] Add `agent_mvp` target in `makedir/Makefile` that executes batch fix + re-lint and fails CI on non-zero exit code or remaining Safe violations.
