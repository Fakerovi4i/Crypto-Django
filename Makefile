.PHONY: up down logs build test shell static ps errors bash stop superuser start whoami ruff-fix ruff-check ruff-format migrate tables logs_app psql fill_500

# Запуск контейнера и тесты
up:
	docker compose up -d

# Создать при первом запуске
superuser:
	docker compose exec crypto_app python manage.py createsuperuser

migrate:
	docker compose exec crypto_app python manage.py migrate crypto

test:
	docker compose exec crypto_app python manage.py test -v 2 --failfast --settings=config.settings_test

ruff-fix:
	docker compose exec crypto_app ruff check . --fix

ruff-check:
	docker compose exec crypto_app ruff check .

ruff-format:
	docker compose exec crypto_app ruff format --check .

mypy:
	docker compose exec crypto_app mypy --no-incremental .


# Docker
down:
	docker compose down

stop:
	docker compose stop

start:
	docker compose up -d

build:
	docker compose up -d --build

logs:
	docker compose logs -f

logs_app:
	docker compose logs crypto_app --tail=100 -f

ps:
	docker compose ps

errors:
	docker compose logs crypto_app | grep -i error || true

bash:
	docker compose exec crypto_app bash

whoami:
	docker compose exec crypto_app whoami


# Вспомогательное
shell:
	docker compose exec crypto_app python manage.py shell_plus --print-sql

static:
	docker compose exec crypto_app python manage.py collectstatic --noinput

tables:
	docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "\dt"'

psql:
	docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB'

fill_500:
	docker compose exec crypto_app python manage.py fill_500_snapshots