FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py voice_analysis_bridge.py connection_lifecycle.py ./
COPY config ./config
COPY interfaces ./interfaces
COPY pipeline ./pipeline
COPY providers ./providers

RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

CMD ["sh", "-c", "exec uvicorn main:app --host '' --port ${PORT}"]
