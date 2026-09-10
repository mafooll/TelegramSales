.DEFAULT_GOAL := check
.PHONY: lint format typecheck test check run db-shell db-reset migration migrate downgrade history

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
