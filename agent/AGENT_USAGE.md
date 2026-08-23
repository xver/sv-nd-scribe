# SV ND Scribe AI Agent — Usage & Architecture Guide

The **SV ND Scribe AI Agent** is an AI-assisted fixer layered on top of the SystemVerilog NaturalDocs linter. It automatically analyzes linter violations and proposes or applies deterministic and LLM-assisted fixes directly in source files.

---

## Quick Start (CLI)

```bash
# Check agent status and connectivity
python3 -m agent --status

# Deterministic batch fix (CI mode, no backup files)
python3 -m agent --llm none --batch --no-backup -f manifest.f

# Dry-run preview (prints proposed diffs without writing to disk)
python3 -m agent --llm none --dry-run tests/test_bad_sv/nd_driver.sv

# Restrict to specific rules
python3 -m agent --rules ND-009,WKL-005 --batch -f manifest.f
```

---

## Python API Usage

```python
from agent import ScribeAgent

agent = ScribeAgent(config_file="agent_config.json")

# Execute deterministic batch fix on a set of files
exit_code = agent.run(
    files=["my_driver.sv", "my_pkg.sv"],
    mode="batch",
    rules_filter=["ND-001", "ND-009"],
    llm_provider="none",
    no_backup=False,
    dry_run=False,
    json_output=False
)
```

---

## LLM Provider Setup

### 1. `none` — Deterministic Fallback (Default for Phase 1 MVP)
Runs all 30 deterministic safe rules without network calls or API keys.

```bash
python3 -m agent --llm none --batch -f manifest.f
```

### 2. `openai` — OpenAI / Azure OpenAI
Requires `OPENAI_API_KEY` environment variable.

```bash
export OPENAI_API_KEY="sk-..."
python3 -m agent --llm openai:gpt-4o my_design.sv
```

### 3. `ollama` — Local Ollama Models
Requires an Ollama instance (default host: `http://localhost:11434`).

```bash
export OLLAMA_HOST="http://localhost:11434"
python3 -m agent --llm ollama:llama3.2 my_design.sv
```

*(Note: `anthropic` and `google` providers are Phase 2 planned additions.)*

---

## File Header Defaults (ND-001)

Configure default file header parameters in `agent_config.json`:

```json
{
  "agent": {
    "header_defaults": {
      "company": "IC Verimeter",
      "author": "v@ic-verimeter.com",
      "legal": "Licensed under the MIT License. See LICENSE in project root."
    }
  }
}
```

Any missing header field defaults to a `TODO_<FIELD>` placeholder sentinel line (e.g. `TODO_LEGAL`).

---

## VS Code Extension Integration

In VS Code:
1. Diagnostics from `sv-nd-scribe` display real-time linting errors.
2. Clicking the lightbulb icon (`Ctrl+.`) on any violation opens Code Actions:
   - `💡 SV_Scribe: Fix (deterministic)`: Applies fix directly.
   - `🤖 SV_Scribe: Fix with AI (<provider>)`: Only active when `agentLlmProvider != "none"`.
3. Command Palette (`Ctrl+Shift+P`):
   - `SV_Scribe: Fix Current File`
   - `SV_Scribe: Batch Fix Current File`
   - `SV_Scribe: Show Agent Status`

---

## Skills Reference

| Skill Directory | Applies To | Description |
|---|---|---|
| `nd_comment` | ND-004, ND-007–018, ND-020–022, ND-025–026, ND-028–032 | Full §27 keyword table; general NaturalDocs comment generation |
| `file_header` | ND-001 | `/* */` header block with all required fields (§2) |
| `group_heading` | ND-006 | `// Group:` section headings with standard name sets (§4) |
| `function_task` | ND-017, ND-030 | Function/Task + Parameters/Returns + extern impl (§16–§18) |
| `variable_doc` | ND-023, ND-012 | `// Variable:` for signals, ports, parameters (§9, §12) |
| `type_doc` | ND-008, ND-010, ND-011 | enum, struct, union, package, typedef (§6, §8–§11) |
| `coverage_doc` | ND-020, ND-021, ND-022 | constraint, covergroup, coverpoint (§13–§15) |
| `sv_constructs` | ND-013, ND-014, ND-025, ND-026, ND-029, ND-031, ND-032 | interface, module, checker, bind, program, clocking, modport (§19, §20, §23) |
| `assertion_property` | ND-015 | Property and labelled assertion (§22) |
| `process_assign` | ND-027, ND-028 | `// process:` and `// assign:` (§23, §25) |
| `triage` | `*` (all rules) | Priority ranking for batch fix ordering |
| `inline_doc` | ND-012, ND-023, ND-024, ND-027 | Inline `//` documentation |

---

## Safety Tiers (sv_documentation_rules.md reference)

| Tier | Description | Modes |
|---|---|---|
| `safe` | Fully deterministic insertion/format fix | `--batch`, `--interactive` |
| `interactive` | Requires human review | `--interactive` only |
| `unsafe` | Report-only — no auto-fixer (rename risk) | Neither |

