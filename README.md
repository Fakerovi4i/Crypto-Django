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


### Запуск через Docker (рекомендуется)

```bash
make build up     # собрать образы и поднять контейнеры
make superuser  # создать админа (опционально)
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
