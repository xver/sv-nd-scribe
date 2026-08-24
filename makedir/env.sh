#!/usr/bin/env bash
# SV ND Scribe Shell Environment
# Source with: source makedir/env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export SVND_SCRIBE_HOME="${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
export SV_ND_SCRIBE_PROJECT_CONFIG="${PROJECT_ROOT}/linter/configs"
