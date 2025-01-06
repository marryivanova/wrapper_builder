# Используем базовый образ
FROM alpine:latest

# Устанавливаем версию Python
RUN apk add --no-cache python3 py3-pip

# Копируем файл в контейнер
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Определяем команду по умолчанию
CMD ["python3", "-c", "print('Hello from Docker!')"]