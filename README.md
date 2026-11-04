# Crypto Analyzer API

### Установка локально

```bash
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser
```
### Необходимая инфраструктура:

- Python ≥ 3.14
- PostgreSQL
- Redis
- Docker + Docker Compose (для запуска в контейнерах)


### Запуск через Docker (настройка ELK в блоке Observability)

```bash
make build up     # собрать образы и поднять контейнеры
make superuser  # создать админа (опционально)
make fetch     # Создать первый снимок
```

### Локальный запуск (без Docker)

```bash
pip install -r requirements.txt
source venv/bin/activate

cd config
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

##### Для прода
```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile - \
  --error-logfile - \
  --no-control-socket
```


### Celery
###### (В Docker — поднимается автоматически)

```bash     
# worker
celery -A config worker -l info

# планировщик (в отдельном терминале)
celery -A config beat -l info
```

## Полезные ссылки
###### _При запуске **через Docker** (nginx на порту 80):_

- API: http://localhost/api/v1/
- Swagger: http://localhost/api/v1/docs/
- JWT: http://localhost/api/token/
- Админка: http://localhost/admin/

###### _При **локальном запуске** (gunicorn на 8000):_

- API: http://localhost:8000/api/v1/
- Swagger: http://localhost:8000/api/v1/docs/
- JWT: http://localhost:8000/api/token/

# Observability (метрики, логи, ошибки)

Стек поднимается вместе с остальными контейнерами через Docker (`make build up`).

### 1. Подготовка `.env`

Переменные, которые нужны для observability:

```env
GRAFANA_PASSWORD=...      # пароль admin в Grafana
ELASTIC_PASSWORD=...      # пароль пользователя elastic (Elasticsearch / Kibana / Logstash)
SENTRY_DSN=               # DSN проекта из sentry.io; если пусто — Sentry не инициализируется
KIBANA_SERVICE_TOKEN=     # токен из kibana-api-token (шаг создания ниже)
```

### 2. Запуск и проверка

```bash
docker compose up elasticsearch
docker compose ps # дождаться, пока elasticsearch станет healthy
# создать service-токен для Kibana  (подставить свой пароль elastic)
curl -X POST -u elastic:<ELASTIC_PASSWORD> "http://localhost:9200/_security/service/elastic/kibana/credential/token/kibana-api-token?pretty"
make build up
```
Импортировать файл в UI кибана \docker\kibana\saved_objects.ndjson


### 3. Доступ к сервисам

| Сервис | URL                                 | Доступ |
|---|-------------------------------------|---|
| Grafana | http://localhost/grafana/           | логин `admin`, пароль `GRAFANA_PASSWORD` |
| Prometheus | http://localhost/prometheus/        | без авторизации |
| Prometheus targets | http://localhost/prometheus/targets | job `crypto_app` должен быть UP |
| Метрики приложения | http://localhost:8000/metrics       | только с хоста; через nginx (порт 80) закрыто |
| Health-check | http://localhost/health/            | 200 `ok` или 503 `degraded` |
| Kibana | http://localhost:5601               | логин `elastic`, пароль `ELASTIC_PASSWORD` |
| Elasticsearch | http://localhost:9200               | логин `elastic`, пароль `ELASTIC_PASSWORD` |
| Logstash | http://localhost:9600 (API)         | — |
| Sentry | https://sentry.io                   | свой проект, DSN в `SENTRY_DSN` |


### 4. Kibana: импорт настроек (Опционально)

После чистого старта импортировать в Kibana: Data View `django-logs-*`, Saved Search `errors-only`, `user-activity`, дашборд - `Django logs`.

1. Открыть Kibana: http://localhost:5601 (логин `elastic`, пароль `ELASTIC_PASSWORD`).
2. Stack Management → Saved Objects → **Import**.
3. Выбрать файл из проекта по пути `docker/kibana/saved_objects.ndjson`.


То же командой:

```bash
curl -X POST -u elastic:<ELASTIC_PASSWORD> \
  "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  --form file=@docker/kibana/saved_objects.ndjson
```