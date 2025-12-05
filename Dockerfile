FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install aiogram aiohttp

CMD ["python", "bot.py"]
