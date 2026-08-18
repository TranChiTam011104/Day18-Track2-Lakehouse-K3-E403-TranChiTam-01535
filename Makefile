## Day 18 Lakehouse Lab — student UX
## Two paths: lightweight (default, pure Python) and Spark (Docker, optional).

CONDA_ENV   := env
PY          := conda run -n $(CONDA_ENV) python
PIP         := conda run -n $(CONDA_ENV) pip
JUPYTER     := conda run -n $(CONDA_ENV) python -m jupyterlab
JUPYTEXT    := conda run -n $(CONDA_ENV) jupytext
PYTEST      := conda run -n $(CONDA_ENV) pytest
COMPOSE    := docker compose -f docker/docker-compose.yml

.DEFAULT_GOAL := help

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nConda path (default):\n"} \
	      /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ─────────────────────────────────────────────────────────────
# Conda path (default) — pure Python, no Docker, no JVM
# ─────────────────────────────────────────────────────────────

setup: ## [conda] Install deps into existing conda env
	@$(PIP) install -q -r requirements.txt
	@$(JUPYTEXT) --to notebook --update notebooks/*.py 2>/dev/null || $(JUPYTEXT) --to notebook notebooks/*.py
	@echo ""
	@echo "  ✓ Setup complete. Activate env: conda activate $(CONDA_ENV)"
	@echo "  Then run 'make smoke' then 'make lab'."

smoke: ## [lite] ~15-second end-to-end smoke test (Delta + Iceberg + vectors)
	@$(PY) scripts/verify_lite.py

test: ## [lite] Run the pytest suite the instructor grades against
	@$(PYTEST) -q

lab: ## [conda] Open Jupyter Lab on http://localhost:8888
	@$(JUPYTEXT) --to notebook --update notebooks/*.py 2>nul || (call )
	@cd notebooks && $(PY) -m jupyter lab --no-browser

data: ## [lite] Generate 200K-row Bronze sample for NB4
	@$(PY) scripts/generate_data_lite.py

data-ai: ## [lite] Generate multimodal + agent-trajectory sample for NB7/NB8
	@$(PY) scripts/generate_ai_data.py

run-all: ## [lite] Execute every notebook headlessly (what CI does)
	@$(PY) scripts/run_all.py

simulate: ## [lite] Abuse the lab the way students do (12 scenarios; SIM_FAST=1 to skip venv builds)
	@$(PY) tests/simulate_students.py

clean: ## [conda] Wipe conda env + lakehouse data
	conda env remove -n $(CONDA_ENV) -y 2>nul || (call )
	@cmd /c "rmdir /s /q _lakehouse 2>nul & del /q notebooks\.ipynb_checkpoints 2>nul & rmdir /s /q .pytest_cache 2>nul & exit /b 0"

# ─────────────────────────────────────────────────────────────
# Spark on Apple `container` (optional) — macOS 15+, Apple silicon
# Same 3-service stack as the compose path, driven by `container run`,
# because Apple's runtime has no compose plugin and no Docker socket.
# ─────────────────────────────────────────────────────────────

AC := scripts/apple_container.sh

apple-up: ## [apple] Start MinIO + buckets + Spark/Jupyter via Apple `container`
	@$(AC) up

apple-smoke: ## [apple] Run scripts/verify.py in the Spark container
	@$(AC) smoke

apple-data: ## [apple] Generate the 1M-row Bronze table via Spark
	@$(AC) data

apple-status: ## [apple] Show containers + MinIO's injected IP
	@$(AC) status

apple-down: ## [apple] Stop and remove containers (MinIO data kept)
	@$(AC) down

apple-clean: ## [apple] Same as apple-down, plus delete _minio-data/
	@$(AC) clean

# ─────────────────────────────────────────────────────────────
# Spark + Docker path (optional, production-fidelity)
# ─────────────────────────────────────────────────────────────

spark-up: ## [spark] Start MinIO + Spark/Jupyter (Docker — first run pulls ~2 GB)
	$(COMPOSE) up -d
	@echo "  Jupyter → http://localhost:8888 (token: lakehouse)"
	@echo "  MinIO   → http://localhost:9001 (minioadmin / minioadmin)"

spark-smoke: ## [spark] Smoke test inside Spark container
	$(COMPOSE) exec -T spark python /workspace/scripts/verify.py

spark-data: ## [spark] Generate 1M-row Bronze (Spark version)
	$(COMPOSE) exec -T spark python /workspace/scripts/generate_data.py

spark-down: ## [spark] Stop Docker stack (data persists)
	$(COMPOSE) down

spark-clean: ## [spark] Stop AND wipe MinIO + ivy cache
	$(COMPOSE) down -v

.PHONY: help setup smoke test lab data data-ai run-all clean \
        simulate apple-up apple-smoke apple-data apple-status apple-down apple-clean \
        spark-up spark-smoke spark-data spark-down spark-clean
