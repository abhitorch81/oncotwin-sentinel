.PHONY: api web test check

api:
	uvicorn apps.api.app.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	python3 -m unittest discover -s apps/api/tests -v

check:
	python3 -m compileall -q apps/api/app
	python3 -m unittest discover -s apps/api/tests -v

