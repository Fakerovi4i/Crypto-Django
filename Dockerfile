FROM python:3.14-slim
RUN groupadd -r group_django && useradd -r -g group_django user_django
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-metrics
RUN pip install --upgrade pip
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user_django:group_django . .

# Создаем заранее 2 папки для статики и метрик
RUN mkdir -p /app/config/staticfiles "$PROMETHEUS_MULTIPROC_DIR"
# Задаем владельца папок
RUN chown -R user_django:group_django /app "$PROMETHEUS_MULTIPROC_DIR"
USER user_django:group_django

WORKDIR /app/config

EXPOSE 8000
