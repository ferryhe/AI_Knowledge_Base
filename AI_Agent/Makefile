.PHONY: help setup index ask pipeline

VENV?=.venv
SOURCE?=../Knowledge_Base_MarkDown

ifeq ($(OS),Windows_NT)
	PY?=$(VENV)/Scripts/python.exe
	PIP?=$(VENV)/Scripts/pip.exe
else
	PY?=$(VENV)/bin/python
	PIP?=$(VENV)/bin/pip
endif

help:
	@echo "Targets:"
	@echo "  setup      - create virtualenv and install dependencies"
	@echo "  index      - build FAISS index from Knowledge_Base_MarkDown"
	@echo "  ask q='?'  - query the index from the command line"
	@echo "  pipeline   - instructions for Open WebUI Pipelines integration"

$(VENV)/.stamp: requirements.txt
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	@touch $(VENV)/.stamp

setup: $(VENV)/.stamp

index: setup
	$(PY) scripts/build_index.py --source $(SOURCE)

ask: setup
	@if [ -z "$$q" ]; then echo "Usage: make ask q='your question'"; exit 1; fi
	$(PY) scripts/ask.py "$$q"

pipeline:
	@echo "Use scripts/responses_pipeline.py inside Open WebUI Pipelines."
	@echo "Mount knowledge_base.faiss and knowledge_base.meta.pkl into /data or update INDEX_PATH/META_PATH env vars."
