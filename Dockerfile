FROM python:3.11-slim

# Установка часового пояса
ENV TZ=Asia/Vladivostok
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Установка зависимостей
RUN pip install fastapi uvicorn pydantic

# Копируем код
COPY main.py .

# Запуск на порту 8090
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]