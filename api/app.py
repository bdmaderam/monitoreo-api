import json
import logging
import math
import os
import random
import time

import psutil
from flask import Flask, Response, g, jsonify, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               generate_latest)

app = Flask(__name__)
APP_NAME = os.getenv("APP_NAME", "api-monitoreo")
ERROR_RATE = float(os.getenv("ERROR_RATE", "0.3"))  # prob. de fallo en /api/error

# ---------- Logging estructurado (JSON a stdout) ----------
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("api")

# ---------- Métricas ----------
REQUESTS = Counter(
    "http_requests_total", "Total de requests HTTP",
    ["method", "endpoint", "status"])
LATENCY = Histogram(
    "http_request_duration_seconds", "Latencia de requests en segundos",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 2.5, 3, 5))
IN_PROGRESS = Gauge(
    "http_requests_in_progress", "Requests que se están procesando ahora",
    ["endpoint"])
CPU = Gauge("system_cpu_percent", "Uso de CPU del sistema (%)")
MEM = Gauge("system_memory_percent", "Uso de memoria del sistema (%)")
PROC_MEM = Gauge("api_process_memory_bytes", "Memoria RSS del proceso de la API")
ITEMS = Counter("api_items_creados_total", "Items creados desde /api/items")

proc = psutil.Process()
psutil.cpu_percent(None)  # primera lectura de calibración

ITEMS_DB = [{"id": i, "nombre": f"item-{i}"} for i in range(1, 11)]


def endpoint_label():
    return request.url_rule.rule if request.url_rule else "no_encontrado"


@app.before_request
def inicio():
    if request.path == "/metrics":
        return
    g.start = time.perf_counter()
    g.endpoint = endpoint_label()
    IN_PROGRESS.labels(g.endpoint).inc()


@app.after_request
def fin(resp):
    if request.path == "/metrics" or not hasattr(g, "start"):
        return resp
    dur = time.perf_counter() - g.start
    REQUESTS.labels(request.method, g.endpoint, str(resp.status_code)).inc()
    LATENCY.labels(request.method, g.endpoint).observe(dur)
    IN_PROGRESS.labels(g.endpoint).dec()
    log.info(json.dumps({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "method": request.method,
        "endpoint": g.endpoint, "status": resp.status_code,
        "duration_ms": round(dur * 1000, 2)}))
    return resp


@app.errorhandler(Exception)
def error_generico(e):
    code = getattr(e, "code", 500)
    return jsonify(error=str(e)), code


# ---------- Endpoints ----------
@app.get("/")
def raiz():
    return jsonify(app=APP_NAME, mensaje="API de monitoreo funcionando",
                   endpoints=["/", "/api/datos", "/api/lento", "/api/error",
                              "/api/items", "/api/calculo/<n>", "/health", "/metrics"])


@app.get("/api/datos")
def datos():
    return jsonify(temperatura=round(random.uniform(15, 30), 1),
                   humedad=random.randint(30, 90), ts=time.time())


@app.get("/api/lento")
def lento():
    time.sleep(random.uniform(2, 3))
    return jsonify(mensaje="Procesamiento lento terminado")


@app.get("/api/error")
def con_error():
    if random.random() < ERROR_RATE:
        return jsonify(error="Fallo simulado"), 500
    return jsonify(mensaje="Esta vez salió bien")


@app.route("/api/items", methods=["GET", "POST"])
def items():
    if request.method == "POST":
        nuevo = {"id": len(ITEMS_DB) + 1, "nombre": f"item-{len(ITEMS_DB) + 1}"}
        ITEMS_DB.append(nuevo)
        ITEMS.inc()
        return jsonify(nuevo), 201
    return jsonify(ITEMS_DB[-20:])


@app.get("/api/calculo/<int:n>")
def calculo(n):
    n = min(n, 200000)
    return jsonify(n=n, resultado=sum(math.sqrt(i) for i in range(n)))


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/metrics")
def metrics():
    CPU.set(psutil.cpu_percent(None))
    MEM.set(psutil.virtual_memory().percent)
    PROC_MEM.set(proc.memory_info().rss)
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, threaded=True)
