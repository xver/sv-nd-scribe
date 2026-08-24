# SV ND Scribe - VS Code Extension ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](../scribe_logo.jpg)

← [Back to main README](../README.md)


Real-time SystemVerilog in-editor diagnostic feedback and automated Quick Fix actions utilizing the **SV ND Scribe** linter and AI agent.

## Features

- **Real-Time Linting**: In-editor diagnostic underlines for all 41 NaturalDocs documentation rules and Wellknown SystemVerilog style guidelines on file save or open.
- **Interactive Quick Fixes (`Ctrl+.` / `Cmd+.` / 💡)**:
  - **Single Rule Fix**: Instant fix for the specific diagnostic at your cursor.
  - **Batch Auto-Fix**: Automatically fix all safe issues across the current file in one click (`SV_Scribe: Fix all auto-fixable issues in file`).
- **File Header Template Management**:
  - **Overwrite Header**: Replace/re-apply the standard corporate file header from template directly from the Quick Fix lightbulb or Command Palette.
  - **Open Template**: Directly open and edit `header_template.txt` in the editor.
  - **Reset Template**: Restore the default built-in header template at any time.
- **Environment & Workspace Customization**: Configure custom environment variables (`SVND_SCRIBE_HOME`, `SV_ND_SCRIBE_PROJECT_CONFIG`) and interpreter paths in settings.
- **Automated Workspace Setup**: Single-command setup of `.vscode/settings.json`, `.env`, terminal environment variables, and shell environments via `setup_workspace.py`.

---

## Requirements

1. **Python 3** (3.8+)
2. **Verible** - specifically `verible-verilog-syntax` installed in your `PATH` (or set `VERIBLE_HOME`).
3. The `sv-nd-scribe` package downloaded to your machine with `SVND_SCRIBE_HOME` pointing to its root directory.

---

## Installation

Install the packaged `.vsix` file using the VS Code CLI or Extensions panel:

```bash
code --install-extension vscode/sv-nd-scribe-vscode-0.1.4.vsix
```

Or via VS Code UI:
1. Press `Ctrl+Shift+P` (macOS: `Cmd+Shift+P`) to open the Command Palette.
2. Type and select **`Extensions: Install from VSIX...`**.
3. Select `sv-nd-scribe-vscode-0.1.4.vsix` and click **Install**.

---

## Quick Workspace Configuration

Automatically configure `.vscode/settings.json`, terminal environment variables, and shell scripts:

```bash
cd makedir
make setup_workspace
# or run directly:
python3 setup_workspace.py
```

---

## Configuration

Configure the extension via VS Code Settings (`Ctrl+,`) by searching for `sv-nd-scribe`:

| Setting | Default | Description |
|---|---|---|
| `sv-nd-scribe.linterPath` | `""` | Absolute path to `linter.py`. If left blank, automatically falls back to `$SVND_SCRIBE_HOME/linter/linter.py`. |
| `sv-nd-scribe.agentPath` | `""` | Absolute path to `agent` module or `agent.py`. If left blank, falls back to `$SVND_SCRIBE_HOME/agent`. |
| `sv-nd-scribe.pythonPath` | `python3` | Path to the Python interpreter. |
| `sv-nd-scribe.enableQuickFix` | `true` | Enable or disable Code Action Quick Fix (`Ctrl+.` / lightbulb) suggestions. |
| `sv-nd-scribe.env` | `{}` | Key-value dictionary of environment variables passed to linter and agent processes (e.g. `SVND_SCRIBE_HOME`, `SV_ND_SCRIBE_PROJECT_CONFIG`). |
| `sv-nd-scribe.runOn` | `onSave` | When to trigger linting: `onSave` or `onOpen`. |

---

## Commands

Access these commands via the VS Code Command Palette (`Ctrl+Shift+P`):

| Command | Title | Description |
|---|---|---|
| `sv-nd-scribe.fix` | **`SV_Scribe: Fix all auto-fixable issues in file`** | Run batch auto-fixer on the active document. |
| `sv-nd-scribe.fixRule` | **`SV_Scribe: Fix specific rule in file`** | Fix a specific rule violation in the active document. |
| `sv-nd-scribe.overwriteHeaderFromTemplate` | **`SV_Scribe: Overwrite File Header from Template`** | Force overwrite the active file's header using the active template. |
| `sv-nd-scribe.openHeaderTemplate` | **`SV_Scribe: Open Header Template to Edit`** | Open `header_template.txt` in the editor. |
| `sv-nd-scribe.resetHeaderTemplate` | **`SV_Scribe: Reset Header Template to Default`** | Reset `header_template.txt` to the default factory template. |
| `sv-nd-scribe.lint` | **`SV_Scribe: Lint`** | Manually run linter on the active document. |
| `sv-nd-scribe.clear` | **`SV_Scribe: Clear`** | Clear all diagnostic underlines from the active document. |
| `sv-nd-scribe.lintAll` | **`SV_Scribe: Lint_All`** | Run linter across all currently open SystemVerilog documents. |
| `sv-nd-scribe.status` | **`SV_Scribe: Status`** / **`Verify linter installation`** | Verify environment health and dependencies. |

---

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs and feature requests to [GitHub Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter
