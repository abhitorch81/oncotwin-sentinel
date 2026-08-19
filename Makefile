.PHONY: install run test smoke zip

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/uvicorn backend.app.main:app --reload --port 8080

test:
	.venv/bin/pytest -q

smoke:
	bash scripts/07_smoke_test.sh

zip:
	cd .. && zip -qr oncotwin-datahub-complete.zip oncotwin-datahub-complete -x '*/.venv/*' '*/__pycache__/*' '*/.env'

