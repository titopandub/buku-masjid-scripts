VENV   := .venv
PYTHON := $(VENV)/bin/python

.PHONY: setup login list report report-clipboard add-pemasukan add-pengeluaran \
        lookup-books lookup-categories lookup-partners lookup-bank-accounts import-csv

setup:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --quiet --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	@echo ""
	@echo "Done. Copy .env.script.example to .env.script and fill in your credentials."

login:
	$(PYTHON) lookup.py books --relogin

list:
	$(PYTHON) list_transactions.py $(ARGS)

report:
	$(PYTHON) whatsapp_report.py $(ARGS)

report-clipboard:
	$(PYTHON) whatsapp_report.py --clipboard $(ARGS)

add-pemasukan:
	$(PYTHON) transaction.py pemasukan $(ARGS)

add-pengeluaran:
	$(PYTHON) transaction.py pengeluaran $(ARGS)

lookup-books:
	$(PYTHON) lookup.py books

lookup-categories:
	$(PYTHON) lookup.py categories $(ARGS)

lookup-partners:
	$(PYTHON) lookup.py partners $(ARGS)

lookup-bank-accounts:
	$(PYTHON) lookup.py bank-accounts

import-csv:
	$(PYTHON) import_csv.py $(ARGS)
