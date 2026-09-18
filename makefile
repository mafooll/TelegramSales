.DEFAULT_GOAL := check
.NOTPARALLEL:
.PHONY: lint format typecheck test check quick run db-shell db-reset migration migrate downgrade history backup backups restore

DC := docker compose

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

typecheck:
	uv run basedpyright

test:
	uv run pytest

check: lint typecheck test

quick:
	uv run ruff check --quiet src tests
	uv run basedpyright
	uv run pytest -x -q -m "not db"

run:
	uv run telegramsales-bot

db-shell:
	$(DC) exec postgres psql -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-telegramsales}

db-reset:
	$(DC) down -v
	$(DC) up -d postgres

migration:
	uv run alembic revision --autogenerate -m "$(m)"

migrate:
	uv run alembic upgrade head

downgrade:
	uv run alembic downgrade -1

history:
	uv run alembic history

backup:
	$(DC) run --rm -e BACKUP_ONCE=true backup

backups:
	$(DC) run --rm --entrypoint ls backup -lh /backups

restore:
	$(DC) run --rm --entrypoint /restore.sh backup $(f)
