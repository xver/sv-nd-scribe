# SV ND Scribe AI Agent & MCP Server ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](../scribe_logo.jpg)

← [Back to main README](../README.md)


The **SV ND Scribe AI Agent** is an automated code fixer and AI assistant integration layer built on top of the SystemVerilog NaturalDocs static linter. It analyzes linter diagnostics and applies safe deterministic fixes, generates intelligent docstrings with LLMs, and exposes standard Model Context Protocol (MCP) tools for modern AI coding environments.

---

## Table of Contents

- [Overview & Architecture](#overview--architecture)
- [CLI Quick Start](#cli-quick-start)
- [Command Line Options](#command-line-options)
- [LLM Backends](#llm-backends)
  - [1. none (Deterministic Fallback - Default)](#1-none-deterministic-fallback---default)
  - [2. openai (OpenAI / Azure OpenAI)](#2-openai-openai--azure-openai)
  - [3. ollama (Local Ollama Models)](#3-ollama-local-ollama-models)
- [File Header Template Management](#file-header-template-management)
- [Model Context Protocol (MCP) Server](#model-context-protocol-mcp-server)
  - [Exposed MCP Tools](#exposed-mcp-tools)
  - [Client Integration Configuration](#client-integration-configuration)
- [Python API Usage](#python-api-usage)
- [Safety Tiers](#safety-tiers)

---

## Overview & Architecture

The Agent operates in two complementary modes:
1. **Deterministic Engine**: Executes instant, zero-cost, rule-specific AST/token transforms for all safe rules without requiring network calls or LLM API keys.
2. **LLM-Assisted Engine**: Leverages local (Ollama) or cloud (OpenAI) language models to synthesize context-aware, semantic descriptions for methods, parameters, and constructs based on repository skill rules.

```
┌────────────────────────────────────────────────────────┐
│                   SV ND Scribe Agent                   │
├──────────────────────────┬─────────────────────────────┤
│   Deterministic Fixer    │     LLM Provider Engine     │
│  (30+ Safe Syntax Rules) │   (OpenAI / Ollama / None)  │
├──────────────────────────┴─────────────────────────────┤
│         Model Context Protocol (MCP) Stdio Server      │
└────────────────────────────────────────────────────────┘
```

---

## CLI Quick Start

```bash
# Check agent environment, loaded rules, skills, and LLM status
python3 -m agent --status

# Batch fix all auto-fixable issues deterministically without .bak files (CI mode)
python3 -m agent --llm none --batch --no-backup -f makedir/template_sv.f

# Dry-run preview: display proposed diffs without writing changes to disk
python3 -m agent --dry-run tests/test_bad_sv/nd_driver.sv

# Apply fixes filtered by specific rule IDs
python3 -m agent --rules ND-001,ND-009,WKL-005 --batch tests/test_bad_sv/nd_driver.sv

# Re-apply corporate header template to a file
python3 -m agent --overwrite-header src/my_module.sv
```

---

## Command Line Options

| Option | Description |
|---|---|
| `files ...` | One or more SystemVerilog source files (`.sv`, `.svh`) to analyze and fix. |
| `-f`, `--file-list` | Path to a `.f` manifest file containing lists of source files. |
| `--batch` | Automatically apply all safe deterministic fixes without prompting. |
| `--interactive` | Prompt for user confirmation before applying each proposed fix (default). |
| `--dry-run` | Print proposed unified diffs without modifying files on disk. |
| `--rules <IDS>` | Filter execution to a comma-separated list of rule IDs (e.g. `ND-001,ND-009,WKL-006`). |
| `--llm <PROVIDER>` | Select LLM provider backend: `none` (default), `openai`, or `ollama`. |
| `--no-backup` | Disable generation of `.bak` backup files when writing changes. |
| `--json` | Output execution diagnostics and results in machine-readable JSON. |
| `--overwrite-header` | Overwrite the target file's header block using the active `header_template.txt`. |
| `--open-header-template` | Print the resolved path and content of the active `header_template.txt`. |
| `--reset-header-template` | Restore the active `header_template.txt` to the built-in factory default. |
| `--status` | Perform health checks on LLM connectivity, active rules, and skills paths. |
| `-c`, `--config` | Path to a custom `agent_config.json` configuration file. |

---

## LLM Backends

### 1. `none` (Deterministic Fallback - Default)
* Executes instant deterministic transforms for 30+ rules.
* Requires zero configuration, zero tokens, and no network connectivity.
* Synthesizes standard NaturalDocs boilerplate comments and formats.

```bash
python3 -m agent --llm none --batch -f manifest.f
```

### 2. `openai` (OpenAI / Azure OpenAI)
* Generates natural language descriptions and parameter docs based on SystemVerilog code semantics.
* Requires `OPENAI_API_KEY` environment variable.

```bash
export OPENAI_API_KEY="sk-..."
python3 -m agent --llm openai:gpt-4o my_design.sv
```

### 3. `ollama` (Local Ollama Models)
* Connects to a local Ollama server without sending code to cloud services.
* Requires a running Ollama instance (default: `http://localhost:11434`).

```bash
export OLLAMA_HOST="http://localhost:11434"
python3 -m agent --llm ollama:llama3.2 my_design.sv
```

---

## File Header Template Management

The agent manages the standard `ND-001` file header block using an editable template file (`header_template.txt`) and default values in `agent_config.json`.

### Inspecting and Resetting Templates

```bash
# Print current header template path and content
python3 -m agent --open-header-template

# Reset template back to built-in default
python3 -m agent --reset-header-template
```

### Configuring Header Defaults (`agent_config.json`)

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

---

## Model Context Protocol (MCP) Server

The repository includes a standard Model Context Protocol stdio server (`agent/mcp_server.py`) enabling AI assistants (such as Antigravity, Cursor, Claude Desktop, and VS Code MCP) to inspect and fix SystemVerilog files.

### Exposed MCP Tools

| MCP Tool | Description | Parameters |
|---|---|---|
| `list_violations` | Runs static linter and returns structured JSON diagnostics list. | `files` (array of file paths) |
| `check_file` | Dry-run proposal generator; returns proposed diffs without writing. | `files`, `rules` (optional), `llm_provider` (default: `"none"`) |
| `fix_file` | Applies automated fixes to files in batch mode. | `files`, `rules` (optional), `llm_provider`, `no_backup` (boolean) |
| `get_status` | Returns environment health, loaded rules, skills, and LLM status. | `llm_provider` (default: `"none"`) |

### Client Integration Configuration

Add the server entry to your MCP client configuration (e.g. `~/.config/Claude/claude_desktop_config.json` or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "sv-nd-scribe": {
      "command": "python3",
      "args": ["-m", "agent.mcp_server"],
      "env": {
        "SVND_SCRIBE_HOME": "/path/to/sv-nd-scribe"
      }
    }
  }
}
```

---

## Python API Usage

You can programmatically invoke the agent from custom Python scripts:

```python
from agent import ScribeAgent

agent = ScribeAgent(config_file="agent_config.json")

# Execute batch fix
exit_code = agent.run(
    files=["src/driver.sv", "src/monitor.sv"],
    mode="batch",
    rules_filter=["ND-001", "ND-009", "WKL-006"],
    llm_provider="none",
    no_backup=True,
    dry_run=False
)
```

---

## Safety Tiers

| Tier | Description | Supported Modes |
|---|---|---|
| `safe` | Fully deterministic formatting and comment insertion | `--batch`, `--interactive` |
| `interactive` | Semantic modification requiring human review | `--interactive` only |
| `unsafe` | Semantic renaming risk (e.g., variable renaming) | Diagnostic report only |

---

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs and feature requests to [GitHub Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter
