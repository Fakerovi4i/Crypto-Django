.PHONY: up down restart logs build ruff ruff-fix ruff-format mypy test migrate shell static ps errors bash stop superuser start

# Запуск контейнера и тесты
up:
	docker compose up -d

test:
	docker compose exec crypto_app python manage.py test -v 2 --failfast

# Создать при первом запуске
superuser:
	docker compose exec crypto_app python manage.py createsuperuser


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

ps:
	docker compose ps

errors:
	docker compose logs crypto_app | grep -i error || true

bash:
	docker compose exec crypto_app bash


# Вспомогательное
ruff-check:
	docker compose exec crypto_app ruff check

ruff-fix:
	docker compose exec crypto_app ruff --fix

ruff-format:
	docker compose exec crypto_app ruff format .

mypy:
	docker compose exec crypto_app mypy --no-incremental .

migrate:
	docker compose exec crypto_app python manage.py migrate

shell:
	docker compose exec crypto_app python manage.py shell

static:
	docker compose exec crypto_app python manage.py collectstatic --noinput

