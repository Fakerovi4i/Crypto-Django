# Crypto Analyzer API

### Установка

```bash
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser
```
### Необходимая инфраструктура:

```
- Python >= 3.14,
- PostgreSQL
- Redis
```

### Запуск

```
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 \
  --access-logfile - --error-logfile -
```

###Celery
```
celery -A config worker -l info
```

## Полезные ссылки
### API: [localhost:8000/api/v1/](localhost:8000/api/v1/)

### Swagger: [localhost:8000/api/v1/docs/](localhost:8000/api/v1/docs/)

### JWT: [localhost:8000/api/token/](localhost:8000/api/token/)
