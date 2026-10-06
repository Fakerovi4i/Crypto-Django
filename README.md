# Crypto Analyzer API

### Установка

```bash
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser
```
### Необходимая инфраструктура:

```text
- python >= 3.14,
- redis
```

### Запуск

```bash
gunicorn config.wsgi:application
```

## Полезные ссылки
### API: [localhost:8000/api/v1/](localhost:8000/api/v1/)

### Swagger: [localhost:8000/api/v1/docs/](localhost:8000/api/v1/docs/)

### JWT: [localhost:8000/api/token/](localhost:8000/api/token/)
