.PHONY: all nd lint lint_bad help

MANIFEST := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))template_sv.f
MANIFEST_BAD := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))test_bad_sv.f

all: help

ND_DIR  := $(shell eval echo $(ND_HOME))
ND_EXEC := $(ND_DIR)/NaturalDocs

nd:
	@if [ -z "$(ND_HOME)" ]; then \
		echo "Error: ND_HOME environment variable is not set."; \
		echo "Please export ND_HOME pointing to the directory containing NaturalDocs, e.g.:"; \
		echo "  export ND_HOME=~/tools/NaturalDocs"; \
		exit 1; \
	elif [ ! -f "$(ND_EXEC)" ] && [ ! -x "$(ND_EXEC)" ]; then \
		echo "Error: NaturalDocs executable not found at '$(ND_EXEC)'."; \
		echo "Please check that ND_HOME contains the NaturalDocs executable."; \
		exit 1; \
	fi
	cd ../docs/nd_config && "$(ND_EXEC)" .

PYTHON ?= python3
LOG_FILE ?= linter.log
LOG_BAD_FILE ?= linter_bad.log

lint:
	cd .. && $(PYTHON) -m linter -f $(MANIFEST) -o $(CURDIR)/$(LOG_FILE)

lint_bad:
	cd .. && $(PYTHON) -m linter -f $(MANIFEST_BAD) -o $(CURDIR)/$(LOG_BAD_FILE)

help:
	@echo ""
	@echo "Usage: make [target] [VARIABLE=value]"
	@echo ""
	@echo "Targets:"
	@echo "  all          Run 'nd' and 'lint' targets sequentially"
	@echo "  nd           Generate NaturalDocs HTML documentation (requires ND_HOME)"
	@echo "  lint         Lint production template files (template_sv.f)"
	@echo "  lint_bad     Lint negative-test files (test_bad_sv.f), used to verify all rules fire"
	@echo "  help         Show this help message"
	@echo ""
	@echo "Variables (override on command line, e.g. make lint PYTHON=python3.11):"
	@echo "  ND_HOME      Path to NaturalDocs installation dir (must contain 'NaturalDocs' executable)"
	@echo "  PYTHON       Python interpreter  [default: python3]"
	@echo "  LOG_FILE     Log file for 'lint' target            [default: linter.log]"
	@echo "  LOG_BAD_FILE Log file for 'lint_bad' target        [default: linter_bad.log]"
	@echo ""
