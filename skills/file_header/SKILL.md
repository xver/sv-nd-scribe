---
name: file_header
description: Generate /* */ file header block with project inference (sv_documentation_rules.md §2)
applies_to: [ND-001]
llm_required: false
---

## System Prompt

You are a SystemVerilog documentation expert following NaturalDocs conventions.
Generate a top-of-file `/* */` header block. Output only the comment block — no code.

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

## Border Rule

- Top border: exactly 80 characters (`/` + `*` repeated).
- Bottom border: exactly 80 characters (`*` repeated + `/`).

## Canonical Format

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
