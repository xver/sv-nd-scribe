# SV ND Scribe - VS Code Extension

Real-time SystemVerilog in-editor diagnostic feedback utilizing the **SV ND Scribe** static linter rules.

## Features

- Highlights NaturalDocs documentation violations (`[WKL-007]`).
- Highlights trailing whitespace (`[WKL-006]`), multiple trailing newlines (`[WKL-005]`), and other syntax formatting issues in real-time.
- Supports customizable linter configuration.

## Requirements

1. **Python 3**
2. **Verible** - specifically `verible-verilog-syntax` installed in your PATH.
3. The standalone `sv-nd-scribe` linter package installed at `/home/v/proj/sv-nd-scribe/`.

## Configuration

You can configure this extension via VS Code Settings:

* `sv-nd-scribe.linterPath`: Absolute path to `linter.py` (Default: `/home/v/proj/sv-nd-scribe/linter/linter.py`).
* `sv-nd-scribe.pythonPath`: Path to the python interpreter (Default: `python3`).
* `sv-nd-scribe.runOn`: Trigger execution on save (`onSave`) or when opening documents (`onOpen`).

## Installation

Install the packaged `.vsix` file using the VS Code CLI or Extensions panel:

```bash
code --install-extension sv-nd-scribe-vscode-0.1.0.vsix
```
