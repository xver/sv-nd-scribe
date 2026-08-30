---
name: setup_troubleshooter
description: Diagnose and resolve installation, dependency, environment variable, and workspace configuration issues for SV ND Scribe across Linux, macOS, Windows, and WSL
applies_to: [*]
llm_required: false
---

# Setup & Installation Troubleshooter Skill

This skill guides AI assistants and engineers through diagnosing and automatically resolving environment, dependency, and configuration issues for **SV ND Scribe**.

---

## 1. Automated Quick Diagnosis & Repair

Before manual troubleshooting, run the built-in diagnostic and auto-repair commands:

```bash
# Diagnose all 7 prerequisites programmatically
python3 -m agent --doctor

# Automatically repair configuration, generate .env, .vscode/settings.json, and default config
python3 -m agent --fix-setup
# or:
cd makedir && make setup_workspace
```

---

## 2. 7-Step Diagnostic Matrix & Resolution Playbooks

| Step | Component | Verification Command | Failure Condition & Immediate Remedy |
|---|---|---|---|
| **1** | **Python 3.9+** | `python3 --version` | Python < 3.9 or not found.<br>**Remedy:** See [OS-Specific Installation](#3-os-specific-prerequisites-installation). |
| **2** | **Verible** | `verible-verilog-syntax --version` | Binary not in `PATH` or `VERIBLE_HOME`.<br>**Remedy:** Install Verible releases or set `VERIBLE_HOME`. |
| **3** | **PyYAML** | `python3 -c "import yaml; print(yaml.__version__)"` | ModuleNotFoundError: `No module named 'yaml'`.<br>**Remedy:** `pip install pyyaml` |
| **4** | **Repository Root** | Check existence of `linter/` & `agent/` | Not in git repo or incomplete clone.<br>**Remedy:** `git clone https://github.com/xver/sv-nd-scribe.git` |
| **5** | **SVND_SCRIBE_HOME** | `echo $SVND_SCRIBE_HOME` | Environment variable not exported.<br>**Remedy:** Run `python3 makedir/setup_workspace.py` or export in shell. |
| **6** | **Workspace Config** | Check `.vscode/settings.json`, `.env`, `linter/configs/` | Missing `.env`, `.vscode/settings.json`, or config directory.<br>**Remedy:** `python3 -m agent --fix-setup` |
| **7** | **Linter Health** | `python3 -m linter --status` | Non-zero exit code or module load error.<br>**Remedy:** Ensure `PYTHONPATH` includes repo root. |

---

## 3. OS-Specific Prerequisites Installation

### Linux (Debian / Ubuntu)
```bash
sudo apt update && sudo apt install -y python3 python3-pip
pip3 install pyyaml

# Verible
# Download from https://github.com/chipsalliance/verible/releases
# Extract and add to PATH, e.g.:
# export PATH="/path/to/verible/bin:$PATH"
```

### macOS (Homebrew)
```bash
brew install python verible
pip3 install pyyaml
```

### Windows (PowerShell)
```powershell
# Python from python.org (ensure "Add Python to PATH" is checked)
pip install pyyaml

# Verible: download windows archive from github.com/chipsalliance/verible/releases
# Add extracted directory to User PATH:
[System.Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\path\to\verible\bin", "User")
```

### WSL (Windows Subsystem for Linux)
- A Windows `.exe` build of Verible sitting in your Windows `PATH` is reachable from WSL directly.
- Ensure Python and PyYAML are installed inside the WSL distribution:
  ```bash
  sudo apt update && sudo apt install -y python3 python3-pip
  pip3 install pyyaml
  ```

---

## 4. Common Edge Cases & Troubleshooting

### Issue: `SV_ND_SCRIBE_PROJECT_CONFIG is not a directory`
- **Cause**: `linter/configs/` directory was missing or misconfigured in `.env` / `settings.json`.
- **Fix**: Run `python3 -m agent --fix-setup` to create `linter/configs/lint_config.json` and sync `.env`.

### Issue: User-level VS Code settings override Workspace settings
- **Cause**: An empty `"sv-nd-scribe.env": {}` in Global/User settings overrides Workspace settings.
- **Fix**: Open VS Code Settings (`Ctrl+,`), search for `sv-nd-scribe.env`, and clear the user-level override, or run `SV_Scribe: Verify linter installation` and click **"Fix Now"**.

### Issue: UNC Path separator conflicts under WSL
- **Cause**: VS Code running on Windows with workspace in `\\wsl.localhost\Ubuntu\...`.
- **Fix**: Extension normalizes paths with forward/backward slash handling automatically when `setup_workspace.py` or `python3 -m agent --fix-setup` is executed.