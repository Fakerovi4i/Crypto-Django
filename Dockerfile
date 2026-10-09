FROM python:3.14-slim
RUN groupadd -r group_django && useradd -r -g group_django user_django
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN pip install --upgrade pip
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user_django:group_django . .

RUN mkdir -p /app/staticfiles && chown -R user_django:group_django /app
USER user_django:group_django

WORKDIR /app/config

EXPOSE 8000
