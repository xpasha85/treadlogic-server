FROM python:3.11-slim

# Установка часового пояса
ENV TZ=Asia/Vladivostok
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 1. Сначала копируем requirements и ставим библиотеки (для кэширования слоев)
# (Если файла requirements.txt еще нет, создай его, см. ниже)
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# 2. Теперь копируем ВСЁ остальное (main.py, папку static и т.д.)
COPY . .

# Запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]