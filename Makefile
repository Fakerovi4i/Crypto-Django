.PHONY: up down logs build test migrate shell static ps errors bash stop superuser start whoami redis_keys redis_ttl django_shell

# Запуск контейнера и тесты
up:
	docker compose up -d

test:
	docker compose exec crypto_app python manage.py test -v 2 --failfast --settings=config.settings_test

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

whoami:
	docker compose exec crypto_app whoami


migrate:
	docker compose exec crypto_app python manage.py migrate

shell:
	docker compose exec crypto_app python manage.py shell

static:
	docker compose exec crypto_app python manage.py collectstatic --noinput

redis_keys:
	docker compose exec redis redis-cli -n 2 keys '*'

redis_ttl:
	docker compose exec redis redis-cli -n 2 ttl ':1:$(KEY)'

django_shell:
	docker compose exec crypto_app python manage.py shell_plus --print-sql