FROM python:3.12-slim

WORKDIR /app

# Настройки Python для Docker контейнеров
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Установка системных зависимостей, необходимых для сборки колес (wheels) psycopg2 и работы с сетью
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Кэширование и установка зависимостей Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app/

# Создаем папки для статики и медиафайлов (К4: Фотогалерея) внутри контейнера
RUN mkdir -p /app/src/static /app/src/media

# Открываем порт 8000, на котором работает наше приложение
EXPOSE 8000
