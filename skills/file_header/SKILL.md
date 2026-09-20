---
name: file_header
description: Generate file header block with project inference (supports /* */, //, or mixed styles; sv_documentation_rules.md §2)
applies_to: [ND-001]
llm_required: false
---

## System Prompt

You are a SystemVerilog documentation expert following NaturalDocs conventions.
Generate a top-of-file header block (defaults to canonical `/* */` block comments; single-line `//` or mixed comments are also supported by rule `ND-001`). Output only the comment block — no code.

## Required Fields (sv_documentation_rules.md §2)

All of the following fields are REQUIRED:

| Field | Format | Notes |
|---|---|---|
| `File` | `filename.sv` | Must match actual filename |
| `Company` | Company name | From project config |
| `Author` | `email@example.com` | Email address required; name optional |
| `Description` | Multi-line description | Explain file purpose and contents |
| `Created` | `Month D, YYYY (email)` | Date and author email in parentheses |
| `Updated` | `Month D, YYYY (email)` | Same format as Created |

## Author Resolution Precedence

When populating the `Author` field:
1. Explicit configuration (`agent.header_defaults.author`).
2. Environment variable (`SV_ND_SCRIBE_AUTHOR`).
3. VS Code setting (`sv-nd-scribe.author` in `.vscode/settings.json`).
4. Project configuration (`agent_config.json`).
5. Git identity (`git config user.name` and `git config user.email`).
6. Fallback: `TODO_AUTHOR` (triggers diagnostic warning).

## Supported Formats (Rule ND-001)

Rule `[ND-001]` accepts file headers in any of the following formats:
1. **Canonical Block Comment (`/* */`)**: Standard corporate template with 80-character borders.
2. **Single-Line Comments (`//`)**: Header documented entirely using contiguous `//` lines.
3. **Mixed Comments**: Combination of block comments and single-line comments.

## Canonical Block Format (`/* */`)

- Top border: exactly 80 characters (`/` + `*` repeated).
- Bottom border: exactly 80 characters (`*` repeated + `/`).

```systemverilog
/******************************************************************************
 * File:        <filename>.sv
 *
 * Company:     <company name>
 *
 * Author:      <email address>
 *
 * Description: <brief description of the file's purpose>
 *              <continuation line if needed>
 *
 * Created:     <Month D, YYYY> (<email>)
 *
 * Updated:     <Month D, YYYY> (<email>)
 *
 * Copyright (c) <YYYY> <Company>
 * <License statement>
 ******************************************************************************/
```

## Example (from template/sv/nd_driver.sv)

```systemverilog
/******************************************************************************
 * File:        nd_driver.sv
 *
 * Company:     IC Verimeter
 *
 * Author:      icshunt.help@gmail.com
 *
 * Description: Driver component that converts transactions to pin wiggles.
 *              Implements the UVM driver interface for the protocol.
 *
 * Created:     July 25, 2026 (icshunt.help@gmail.com)
 *
 * Updated:     July 25, 2026 (icshunt.help@gmail.com)
 *
 * Copyright (c) 2026 IC Verimeter
 * Licensed under the MIT license. See LICENSE file in the project root for details.
 ******************************************************************************/
```

## Single-Line Comment Format (`//`)

```systemverilog
//
// File:        <filename>.sv
// Company:     <company name>
// Author:      <email address>
// Description: <brief description of the file's purpose>
// Created:     <Month D, YYYY> (<email>)
// Updated:     <Month D, YYYY> (<email>)
// Copyright (c) <YYYY> <Company>
// <License statement>
//
```

## Mixed Comment Format

```systemverilog
// ============================================================================
/*
 * File:        <filename>.sv
 * Company:     <company name>
 * Author:      <email address>
 * Description: <brief description of the file's purpose>
 */
// Created:     <Month D, YYYY> (<email>)
// Updated:     <Month D, YYYY> (<email>)
// ============================================================================
```

## User Prompt Template

```
Generate a file header for:
  Filename:    {{filename}}
  Company:     {{company}}
  Author:      {{author_email}}
  Description: {{description}}
  Date:        {{date}}

Output only the /* */ header block.
```
