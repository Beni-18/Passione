.PHONY: up down test train freeze

up:
	docker compose up --build

down:
	docker compose down

test:
	cd backend && python -m pytest ../tests -v

# Triggers a real training run through the running API (which calls
# mlcore.train_model() under the hood — docs/INTEGRATION.md Seam 1), rather
# than invoking mlcore directly, so it exercises the same path the UI does.
train:
	curl -s -X POST http://localhost:8000/train -F "file=@data/samples/clean_50.csv" | tee /dev/stderr

# Runs the full hostile-input + contract + reproducibility suite and the
# smoke script, the pre-submission checklist from CLAUDE.md section 7.
freeze: test
	bash scripts/smoke.sh
