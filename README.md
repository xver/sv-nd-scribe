# Welcome to sv-nd-scribe - NaturalDocs and Linting for SystemVerilog! ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](scribe_logo.png)

Never write undocumented or unformatted SystemVerilog again.

The **sv-nd-scribe** toolkit combines:

- **NaturalDocs-based documentation rules**
- **Static linter** for detecting issues in source files
- **AI agent** with deterministic and LLM-assisted auto-fixers
- **Workspace setup doctor** that validates prerequisites and automatically repairs missing configurations
- **Model Context Protocol (MCP) server** for AI assistants/IDEs
- **Curated knowledge base** of 13 SystemVerilog documentation skills
- **VS Code extension** for real-time in-editor feedback

**sv-nd-scribe** is available under the MIT License and can be used without restriction in both open-source and commercial applications.

Also, check out other open-source projects by IC Verimeter:

- [The Shunt](https://github.com/xver/Shunt): An Open Source Client/Server TCP/IP socket-based communication library designed for integrating SystemVerilog simulations with external applications in C, SystemC, and Python.
- [SVDB Gateway](https://github.com/xver/svdb_gateway): A bridge between SystemVerilog and SQLite databases, allowing SystemVerilog code to interact with SQLite through the Direct Programming Interface (DPI).
- [icecream_sv](https://github.com/xver/icecream_sv): IceCream for SystemVerilog!

---

> 🚀 **Fast Track for VS Code users:** Jump directly to the [**VS Code 3-Step Getting Started Guide**](vscode/README.md#getting-started-3-steps) to set up and verify in under 2 minutes.

---

## Documentation Map

Each core subsystem of **sv-nd-scribe** has its own dedicated documentation:

| Component | Description | Documentation Link |
|---|---|---|
| 🔍 **Static Linter** | AST-based static analyzer with `.f` manifest and JSON output support | [**`linter/README.md`**](linter/README.md) |
| 📋 **Linting Rules** | Full catalog of all 41 Wellknown (WKL) and NaturalDocs (ND) rules | [**`linter/rules/RULES.md`**](linter/rules/RULES.md) |
| 🤖 **AI Agent & Auto-Fixer** | Deterministic syntax engine, LLM backends, template manager, setup doctor, and Python API | [**`agent/README.md`**](agent/README.md) |
| 🔌 **MCP Server** | Model Context Protocol server exposing lint, check, and fix tools to AI IDEs | [**`agent/README.md#model-context-protocol-mcp-server`**](agent/README.md#model-context-protocol-mcp-server) |
| 📚 **Skills Knowledge Base** | 13 reference guides, keyword tables, and troubleshooting skills | [**`skills/README.md`**](skills/README.md) |
| 💻 **VS Code Extension** | Real-time diagnostics, Lightbulb (`Ctrl+.`) Quick-Fixes, 7-step verification, and auto-fix | [**`vscode/README.md`**](vscode/README.md) · [⚡ **Quick Start**](vscode/README.md#getting-started-3-steps) |

---

## Getting Started (3 Steps)

Get up and running in under 2 minutes:

---

### Step 1 — Clone the Repository & Check Prerequisites

Clone the **sv-nd-scribe** repository to your local machine:

```bash
git clone https://github.com/xver/sv-nd-scribe.git
cd sv-nd-scribe
```

Ensure the following prerequisites are installed:

1. **Python 3.9+** (`python3 --version` or `python --version`)
   - Linux: `sudo apt update && sudo apt install -y python3 python3-pip`
   - macOS: `brew install python`
   - Windows: Install from [python.org](https://www.python.org/downloads/) (*check "Add Python to PATH"*).
2. **Verible** (`verible-verilog-syntax --version`)
   - Download prebuilt binaries from the [ChipsAlliance Verible releases page](https://github.com/chipsalliance/verible/releases) and ensure `verible-verilog-syntax` is in your `PATH` (or set `VERIBLE_HOME`).
   - *WSL Note:* A Windows `.exe` build of Verible in your Windows `PATH` is reachable in WSL automatically as `verible-verilog-syntax.exe`.
3. **PyYAML**
   ```bash
   pip install pyyaml
   ```

---

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
- `linter/configs/lint_config.json` — Prepares default linter configuration.

---

### Step 3 — Verify Environment & Install VS Code Extension

#### Option A: Terminal Verification with Agent Doctor
```bash
# Source environment variables
source makedir/env.sh

# Run comprehensive environment doctor (7 health checks)
python3 -m agent --doctor
```

> **Auto-Repair:** If any check fails, run `python3 -m agent --fix-setup` to automatically repair missing files and configurations.

#### Option B: VS Code Extension Verification
1. Install the packaged extension:
   ```bash
   code --install-extension vscode/sv-nd-scribe-vscode-0.1.5.vsix
   ```
2. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run:  
   **`SV_Scribe: Verify linter installation`**
3. If any configuration is missing, click **"Auto-Fix with Agent"** directly in the notification.

---

## Quick Start & CLI Reference

### 1. Automation via Makefile

The `makedir/` directory contains automation targets for linting, documentation, testing, and IDE configuration:

```bash
cd makedir

# Auto-configure workspace environment (.vscode/settings.json, .env, shell env)
make setup_workspace

# Check linter dependencies and environment health
make status

# Check AI agent status and LLM connectivity
make agent_status

# Lint production template files
make lint
```

*For complete Makefile options, see [Running the Linter](linter/README.md#cli-command-reference).*

---

### 2. Running the Static Linter

Lint individual files or batch process manifests using standard `.f` files:

```bash
# Check dependencies
python3 -m linter --status

# Lint specific SystemVerilog files
python3 -m linter src/my_module.sv src/my_if.sv

# Batch lint with manifest
python3 -m linter -f makedir/template_sv.f
```

👉 **Full linter documentation**: [**`linter/README.md`**](linter/README.md)  
👉 **Complete rule catalog (41 rules)**: [**`linter/rules/RULES.md`**](linter/rules/RULES.md)

---

### 3. Running the AI Fixer Agent

Automatically resolve linter violations using high-speed deterministic transforms or LLMs:

```bash
# Comprehensive environment health check
python3 -m agent --doctor

# Auto-repair missing workspace settings and configurations
python3 -m agent --fix-setup

# Check agent status and provider configuration
python3 -m agent --status

# Deterministic batch fix (CI/CD mode, no backups)
python3 -m agent --llm none --batch --no-backup -f makedir/template_sv.f

# Dry-run preview: display proposed diffs without writing to disk
python3 -m agent --dry-run tests/test_bad_sv/nd_driver.sv

# Re-apply corporate header template
python3 -m agent --overwrite-header src/my_module.sv
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

* **Setup & Environment**: [`setup_troubleshooter`](skills/setup_troubleshooter/SKILL.md)
* **File & Containers**: [`file_header`](skills/file_header/SKILL.md), [`sv_constructs`](skills/sv_constructs/SKILL.md), [`group_heading`](skills/group_heading/SKILL.md)
* **Methods & Logic**: [`function_task`](skills/function_task/SKILL.md), [`process_assign`](skills/process_assign/SKILL.md), [`assertion_property`](skills/assertion_property/SKILL.md)
* **Data & Types**: [`type_doc`](skills/type_doc/SKILL.md), [`variable_doc`](skills/variable_doc/SKILL.md), [`inline_doc`](skills/inline_doc/SKILL.md), [`coverage_doc`](skills/coverage_doc/SKILL.md)
* **Conventions & Priority**: [`nd_comment`](skills/nd_comment/SKILL.md), [`triage`](skills/triage/SKILL.md)

👉 **Full skills catalog & keyword tables**: [**`skills/README.md`**](skills/README.md)

---

### 6. VS Code Extension

Install the packaged extension for in-editor linting, Lightbulb (`Ctrl+.`) Quick-Fix actions, interactive 7-step setup verification, and header template management:

```bash
# Install the extension
code --install-extension vscode/sv-nd-scribe-vscode-0.1.5.vsix

# Configure workspace environment: .vscode/settings.json, .env, shell env variables
cd makedir && make setup_workspace
```

👉 **VS Code 3-Step Quick Start**: [**`vscode/README.md#getting-started-3-steps`**](vscode/README.md#getting-started-3-steps)  
👉 **Full VS Code extension guide**: [**`vscode/README.md`**](vscode/README.md)

---

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs and feature requests to [GitHub Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter


