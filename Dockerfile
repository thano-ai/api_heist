FROM python:3.11-slim

WORKDIR /app

# Educational lab only — bind localhost in compose / run instructions
ENV DVAPI_HOST=0.0.0.0
ENV DVAPI_PORT=5000
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

WORKDIR /app/backend
EXPOSE 5000

CMD ["python", "app.py"]
