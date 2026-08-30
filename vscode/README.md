# SV ND Scribe - VS Code Extension ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](https://raw.githubusercontent.com/xver/sv-nd-scribe/main/scribe_logo.jpg)

Real-time SystemVerilog in-editor diagnostic feedback and automated Quick Fix actions utilizing the **SV ND Scribe** linter and AI agent.

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
   - Windows: Install from [python.org](https://www.python.org/downloads/) (check *"Add Python to PATH"*).
2. **Verible** (`verible-verilog-syntax --version`)
   - Download prebuilt binaries from the [Verible releases page](https://github.com/chipsalliance/verible/releases) and ensure `verible-verilog-syntax` is in your `PATH` (or set `VERIBLE_HOME`).
   - *WSL Note:* A Windows `.exe` build of Verible in your Windows `PATH` is reachable inside WSL automatically.
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
- `linter/configs/lint_config.json` — Prepares default linter settings with zero warnings.

---

### Step 3 — Install Extension & Verify in VS Code

1. Open the repository folder in VS Code:
   ```bash
   code .
   ```
2. Install the **SV ND Scribe** extension from the VS Code Marketplace (search for `sv-nd-scribe`).
3. Verify your installation by opening the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and selecting:
   **`SV_Scribe: Verify linter installation`**

The interactive checker verifies all 7 prerequisite steps sequentially:

| Check | What It Verifies |
|---|---|
| Step 1 | Python 3.9+ is installed and in PATH |
| Step 2 | `verible-verilog-syntax` is reachable |
| Step 3 | PyYAML package is installed |
| Step 4 | Repository root structure is valid |
| Step 5 | `SVND_SCRIBE_HOME` environment variable is set |
| Step 6 | Workspace `.vscode/settings.json`, `.env`, and config directory are present |
| Step 7 | Linter module initializes cleanly |

> **Troubleshooting & Auto-Fix:** If any check fails, click **"Auto-Fix with Agent"** in the VS Code notification or run `python3 -m agent --fix-setup` from your terminal.

---

### Start Using

1. Open any `.sv` or `.svh` file in VS Code.
2. **On save** (default), the linter highlights documentation and style issues with diagnostic underlines.
3. Click any diagnostic underline and press `Ctrl+.` (macOS: `Cmd+.`) or click the 💡 lightbulb for instant **Quick Fix** suggestions.
4. To fix **all** auto-fixable issues at once, open the Command Palette (`Ctrl+Shift+P`) and run:
   **`SV_Scribe: Fix all auto-fixable issues in file`**

---

<details>
<summary><b>Manual / Advanced Configuration (Click to expand)</b></summary>

### Manual Environment Variables

If you prefer to configure environment variables manually instead of running `setup_workspace.py`:

**Linux / macOS** — add to `~/.bashrc` or `~/.zshrc`:
```bash
export SVND_SCRIBE_HOME="$HOME/proj/sv-nd-scribe"
export PYTHONPATH="$SVND_SCRIBE_HOME:$PYTHONPATH"
export SV_ND_SCRIBE_PROJECT_CONFIG="$SVND_SCRIBE_HOME/linter/configs"
```

**Windows (PowerShell)**:
```powershell
[System.Environment]::SetEnvironmentVariable("SVND_SCRIBE_HOME", "C:\path\to\sv-nd-scribe", "User")
[System.Environment]::SetEnvironmentVariable("PYTHONPATH", "C:\path\to\sv-nd-scribe", "User")
[System.Environment]::SetEnvironmentVariable("SV_ND_SCRIBE_PROJECT_CONFIG", "C:\path\to\sv-nd-scribe\linter\configs", "User")
```

**Manual `.vscode/settings.json` snippet**:
```json
{
  "sv-nd-scribe.linterPath": "${workspaceFolder}/linter/linter.py",
  "sv-nd-scribe.agentPath": "${workspaceFolder}/agent",
  "sv-nd-scribe.pythonPath": "python3",
  "sv-nd-scribe.runOn": "onSave",
  "sv-nd-scribe.enableQuickFix": true,
  "sv-nd-scribe.env": {
    "SVND_SCRIBE_HOME": "${workspaceFolder}",
    "PYTHONPATH": "${workspaceFolder}",
    "SV_ND_SCRIBE_PROJECT_CONFIG": "${workspaceFolder}/linter/configs"
  },
  "python.envFile": "${workspaceFolder}/.env"
}
```

### Command-Line Verification & Diagnostics

```bash
# Check linter status:
python3 -m linter --status

# Run full environment doctor report:
python3 -m agent --doctor

# Run automated workspace repair:
python3 -m agent --fix-setup
```

</details>

---

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
- **Automated Workspace Setup & Doctor**: Single-command setup and diagnosis of `.vscode/settings.json`, `.env`, terminal environment variables, and shell environments via `setup_workspace.py` and `agent --doctor`.

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
| `sv-nd-scribe.status` | **`SV_Scribe: Status`** | Check runtime health and connection status. |
| `sv-nd-scribe.verifyInstallation` | **`SV_Scribe: Verify linter installation`** | Interactive 7-step prerequisites and workspace verifier with Auto-Fix. |

---

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs and feature requests to [GitHub Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter