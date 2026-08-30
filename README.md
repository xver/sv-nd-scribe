# Welcome to sv-nd-scribe - NaturalDocs and Linting for SystemVerilog! ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](scribe_logo.jpg)

Never write undocumented or unformatted SystemVerilog again.

The **sv-nd-scribe** toolkit combines NaturalDocs-based documentation rules, a static linter for detecting issues in source files, an AI agent with deterministic and LLM-assisted auto-fixers, a Model Context Protocol (MCP) server for AI assistants/IDEs, a curated knowledge base of SystemVerilog documentation skills, and a VS Code extension for real-time in-editor feedback. **sv-nd-scribe** is available under the MIT License and can be used without restriction in both open-source and commercial applications.

Also, check out other open-source projects by IC Verimeter:

- [The Shunt](https://github.com/xver/Shunt): An Open Source Client/Server TCP/IP socket-based communication library designed for integrating SystemVerilog simulations with external applications in C, SystemC, and Python.
- [SVDB Gateway](https://github.com/xver/svdb_gateway): A bridge between SystemVerilog and SQLite databases, allowing SystemVerilog code to interact with SQLite through the Direct Programming Interface (DPI).
- [icecream_sv](https://github.com/xver/icecream_sv): IceCream for SystemVerilog!

---

## Documentation Map

Each core subsystem of **sv-nd-scribe** has its own dedicated documentation:

| Component | Description | Documentation Link |
|---|---|---|
| 🔍 **Static Linter** | AST-based static analyzer with `.f` manifest and JSON output support | [**`linter/README.md`**](linter/README.md) |
| 📋 **Linting Rules** | Full catalog of all 41 Wellknown (WKL) and NaturalDocs (ND) rules | [**`linter/rules/RULES.md`**](linter/rules/RULES.md) |
| 🤖 **AI Agent & Auto-Fixer** | Deterministic syntax engine, LLM backends, `--doctor` diagnostics, and template manager | [**`agent/README.md`**](agent/README.md) |
| 🔌 **MCP Server** | Model Context Protocol server exposing lint, check, and fix tools to AI IDEs | [**`agent/README.md#model-context-protocol-mcp-server`**](agent/README.md#model-context-protocol-mcp-server) |
| 📚 **Skills Knowledge Base** | 13 reference guides, keyword tables, and setup troubleshooting agent skill | [**`skills/README.md`**](skills/README.md) |
| 💻 **VS Code Extension** | Real-time diagnostics, Lightbulb (`Ctrl+.`) Quick-Fixes, 7-step Doctor, and Auto-Fix | [**`vscode/README.md`**](vscode/README.md) |

---

## Prerequisites

To use the static linter and agent, ensure the following are installed:

1. **Python 3.9+** (`python3 --version` or `python --version`)
2. **Verible** - specifically the `verible-verilog-syntax` executable.
   - Download Verible from the [ChipsAlliance GitHub releases page](https://github.com/chipsalliance/verible/releases).
   - Ensure `verible-verilog-syntax` (or `verible-verilog-syntax.exe`) is available in your system `PATH` (or set `VERIBLE_HOME`).
   - *Note: In WSL, a Windows installation of Verible (.exe) in your PATH is automatically detected and supported.*
3. **PyYAML** (`pip install pyyaml`)

---

## Quick Start (3 Steps)

### Step 1 — Clone the Repository
```bash
git clone https://github.com/xver/sv-nd-scribe.git
cd sv-nd-scribe
```

### Step 2 — Run Automated Workspace Setup
From the repository root, run the setup automation:

```bash
cd makedir && make setup_workspace
# or:
python3 makedir/setup_workspace.py
```

This single command automatically configures:
- `.vscode/settings.json` — Preconfigures linter and agent paths, terminal environment variables, and `.sv`/`.svh`/`.v` file associations.
- `.env` — Generates workspace root environment file (`SVND_SCRIBE_HOME`, `PYTHONPATH`, `SV_ND_SCRIBE_PROJECT_CONFIG`).
- `makedir/env.sh` — Creates shell sourcing script for terminal command lines (`source makedir/env.sh`).
- `linter/configs/lint_config.json` — Prepares default linter settings with zero warnings.

### Step 3 — Verify & Use
```bash
# Source environment variables for terminal session
source makedir/env.sh

# Run the 7-phase system doctor check
python3 -m agent --doctor

# Run unit test suite (126 tests)
python3 -m unittest discover -s tests
```

---

## Core Capabilities

### 1. Environment Doctor & Auto-Repair

The built-in diagnostic agent validates your complete development stack:

```bash
# Run 7-phase diagnostic report
python3 -m agent --doctor

# Run JSON report (CI/CD integration)
python3 -m agent --doctor --json

# Automatically heal and fix missing workspace configurations
python3 -m agent --fix-setup
```

---

### 2. Running the Static Linter

Lint individual files or batch process manifests using standard `.f` files:

```bash
# Check linter status & environment
python3 -m linter --status

# Lint specific SystemVerilog files
python3 -m linter example/example.sv

# Batch lint with manifest
python3 -m linter -f makedir/template_sv.f
```

👉 **Full linter documentation**: [**`linter/README.md`**](linter/README.md)  
👉 **Complete rule catalog (41 rules)**: [**`linter/rules/RULES.md`**](linter/rules/RULES.md)

---

### 3. Running the AI Fixer Agent

Automatically resolve linter violations using high-speed deterministic transforms or LLMs:

```bash
# Check agent status and LLM connectivity
python3 -m agent --status

# Dry-run preview: display proposed diffs without writing to disk
python3 -m agent --dry-run example/example.sv

# Deterministic batch fix (CI/CD mode, no backups)
python3 -m agent --llm none --batch --no-backup -f makedir/template_sv.f

# Re-apply corporate header template
python3 -m agent --overwrite-header example/example.sv
```

👉 **Full AI agent and CLI guide**: [**`agent/README.md`**](agent/README.md)

---

### 4. Model Context Protocol (MCP) Server

Connect `sv-nd-scribe` tools directly to AI assistants and IDEs (Antigravity, Cursor, Claude Desktop, VS Code MCP):

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

*Tools provided: `list_violations`, `check_file`, `fix_file`, `get_status`.*

👉 **MCP Server guide and tool reference**: [**`agent/README.md#model-context-protocol-mcp-server`**](agent/README.md#model-context-protocol-mcp-server)

---

### 5. NaturalDocs Skills Knowledge Base

A library of 13 modular skills defining syntactic standards, comment structures, and setup diagnostics:

* **File & Containers**: [`file_header`](skills/file_header/SKILL.md), [`sv_constructs`](skills/sv_constructs/SKILL.md), [`group_heading`](skills/group_heading/SKILL.md)
* **Methods & Logic**: [`function_task`](skills/function_task/SKILL.md), [`process_assign`](skills/process_assign/SKILL.md), [`assertion_property`](skills/assertion_property/SKILL.md)
* **Data & Types**: [`type_doc`](skills/type_doc/SKILL.md), [`variable_doc`](skills/variable_doc/SKILL.md), [`inline_doc`](skills/inline_doc/SKILL.md), [`coverage_doc`](skills/coverage_doc/SKILL.md)
* **Conventions & Priority**: [`nd_comment`](skills/nd_comment/SKILL.md), [`triage`](skills/triage/SKILL.md)
* **Setup & Diagnostics**: [`setup_troubleshooter`](skills/setup_troubleshooter/SKILL.md)

👉 **Full skills catalog & keyword tables**: [**`skills/README.md`**](skills/README.md)

---

### 6. VS Code Extension

Install the packaged extension for in-editor linting, Lightbulb (`Ctrl+.`) Quick-Fix actions, 7-step installer verification, and one-click "Auto-Fix with Agent":

```bash
# Install the extension package
code --install-extension vscode/sv-nd-scribe-vscode-0.1.5.vsix
```

1. Open the repository folder in VS Code: `code .`
2. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and select:
   **`SV_Scribe: Verify linter installation`**
3. If any workspace issue is detected, click **"Auto-Fix with Agent"** directly from the notification.

👉 **Full VS Code extension guide**: [**`vscode/README.md`**](vscode/README.md)

---

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs and feature requests to [GitHub Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter

