.PHONY: help install validate validate-negative test clean

PYTHON ?= python3
VENV   ?= .venv
PIP    := $(VENV)/bin/pip
PY     := $(VENV)/bin/python

help:
	@echo "Loop — common targets"
	@echo
	@echo "  make install            create a local venv and install validator deps"
	@echo "  make validate           validate every example against its schema"
	@echo "  make validate-negative  confirm the schemas reject malformed inputs"
	@echo "  make test               run both validators"
	@echo "  make clean              remove the local venv"

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r tools/requirements.txt

install: $(VENV)

validate: $(VENV)
	$(PY) tools/validate.py

validate-negative: $(VENV)
	$(PY) tools/validate_negative.py

test: validate validate-negative

clean:
	rm -rf $(VENV)
