FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 3000
# 1 worker + hilos: las métricas de prometheus_client viven en un solo proceso
CMD ["gunicorn", "-w", "1", "--threads", "8", "-b", "0.0.0.0:3000", "app:app"]
