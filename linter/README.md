# SV ND Scribe Static Linter ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](../scribe_logo.jpg)

← [Back to main README](../README.md)


The **SV ND Scribe Linter** is a fast, standalone static analysis tool for SystemVerilog source code. It validates NaturalDocs documentation formatting and team-wide SystemVerilog coding conventions using AST analysis powered by Verible (`verible-verilog-syntax`).

---

## Table of Contents

- [Quick Start](#quick-start)
- [CLI Command Reference](#cli-command-reference)
- [Manifest File (.f) Batch Mode](#manifest-file-f-batch-mode)
- [Configuration Files](#configuration-files)
- [Rules Reference](#rules-reference)
- [Python Integration](#python-integration)

---

## Quick Start

```bash
# Check linter installation and environment health
python3 -m linter --status

# Lint a single file
python3 -m linter path/to/my_design.sv

# Lint multiple files
python3 -m linter src/pkg.sv src/dut.sv tb/top.sv

# Lint a batch of files using a manifest
python3 -m linter -f makedir/template_sv.f
```

---

## CLI Command Reference

Execute via `python3 -m linter` or `python3 linter/linter.py`:

```bash
python3 -m linter [OPTIONS] [FILES...]
```

### Options

| Option | Description |
|---|---|
| `files ...` | One or more `.sv` / `.svh` files to check. |
| `-f`, `--file-list <FILE>` | Path to a `.f` manifest file containing source file paths. |
| `-c`, `--config <CONFIG>` | Path to a JSON configuration file (e.g. `linter/configs/lint_config.json`). |
| `-o`, `--output <LOG_FILE>` | Redirect linting report to a log file. |
| `--json` | Output results in machine-readable JSON format. |
| `--status` | Check Verible binary availability, environment variables, and rule registry. |
| `-h`, `--help` | Display help message and options. |

---

## Manifest File (.f) Batch Mode

The linter accepts standard EDA `.f` file lists:
* One file path per line.
* Comments starting with `//` or `#` are ignored.
* Compiler options starting with `+` or `-` are automatically skipped.
* Environment variables like `$SVND_SCRIBE_HOME/template/sv/nd_dut.sv` are expanded.

```
# Manifest example (my_project.f)
$MY_PROJ/src/header.svh
$MY_PROJ/src/alu.sv
$MY_PROJ/src/control.sv
```

---

## Configuration Files

The linter can be customized using JSON configuration files (`linter/configs/lint_config.json`). You can disable specific rules or adjust severity levels per project:

```json
{
  "rules": {
    "WKL-007": {
      "enabled": true,
      "max_length": 120
    },
    "ND-002": {
      "enabled": true
    }
  }
}
```

Point to your config using the `-c` flag or `SV_ND_SCRIBE_PROJECT_CONFIG` environment variable:

```bash
export SV_ND_SCRIBE_PROJECT_CONFIG="/path/to/my_config_dir"
```

---

## Rules Reference

The linter implements **41 rules**:
- **9 Wellknown (WKL) Rules**: Style, naming conventions, tab prevention, line length, and single variable declarations (`WKL-001` through `WKL-009`).
- **32 NaturalDocs (ND) Rules**: Comprehensive docstring coverage for every SystemVerilog construct (`ND-001` through `ND-032`).

For the complete rule catalog with descriptions and examples, see **[`linter/rules/RULES.md`](rules/RULES.md)**.

---

## Python Integration

The linter can be embedded directly in Python test benches, CI scripts, or lint suites. See **[`linter/PYTHON_USAGE.md`](PYTHON_USAGE.md)** for API examples.

---

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs and feature requests to [GitHub Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter
