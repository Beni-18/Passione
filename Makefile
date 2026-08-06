.PHONY: up down test train freeze

up:
	docker compose up --build

down:
	docker compose down

test:
	cd backend && python -m pytest ../tests -v

# Trains a model via ml/src/train.py against a CSV, writing an artifact into
# models/. No-op stub until the ml/ side lands — see docs/INTEGRATION.md.
train:
	python ml/src/train.py --csv data/samples/clean_50.csv --seed 42

# Runs the full hostile-input + contract + reproducibility suite and the
# smoke script, the pre-submission checklist from CLAUDE.md section 7.
freeze: test
	bash scripts/smoke.sh
