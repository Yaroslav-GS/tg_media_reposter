FROM python:3.12-alpine

RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

RUN addgroup -S app && adduser -S -G app app
USER app

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
