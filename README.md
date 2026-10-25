# Monitoreo y observabilidad de una API con Prometheus y Grafana

**Nombre:** Brayan Dario Madera Martinez
**Código de estudiante:** 202220042601
**Curso:** Desarrollo de aplicaciones en la nube – Fundación Universitaria Los Libertadores
**Video:** https://fundacionlibertadores-my.sharepoint.com/:v:/r/personal/bdmaderam_libertadores_edu_co/_layouts/15/stream.aspx?id=%2Fpersonal%2Fbdmaderam_libertadores_edu_co%2FDocuments%2FVideo%20Project.mp4&share=cQpVOAuhmFYCQ51X8GOROCYREgUCxN_yeGpKUUujZ7zlpZLu3Q&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0

## Qué es

Una API REST en Python (Flask) instrumentada con `prometheus-client`, un Prometheus que la raspa cada 15 segundos y un Grafana con un dashboard ya provisionado. Todo corre con `docker-compose`. Incluye un script que genera tráfico sintético para ver las métricas moverse.

## Estructura

```
.
├── docker-compose.yml
├── README.md
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── prometheus/
│   ├── prometheus.yml
│   └── alerts.yml
├── grafana/
│   ├── provisioning/        # datasource y proveedor de dashboards
│   └── dashboards/api-monitoreo.json
└── scripts/
    ├── generate-traffic.py
    └── generate-traffic.sh
```

## Cómo ejecutarlo

Requisitos: Docker y Docker Compose.

```bash
docker-compose down -v          # limpiar (opcional)
docker-compose up -d --build
docker-compose ps               # deben salir 3 servicios "Up"
```

| Servicio   | URL                      | Credenciales   |
|------------|--------------------------|----------------|
| API        | http://localhost:3000    | -              |
| Métricas   | http://localhost:3000/metrics | -         |
| Prometheus | http://localhost:9090    | -              |
| Grafana    | http://localhost:3001    | admin / admin  |

El dashboard **Monitoreo API** aparece solo en Grafana (Dashboards), no hay que importar nada.

## Generar tráfico

```bash
python scripts/generate-traffic.py http://localhost:3000 600   # 10 minutos
# o
./scripts/generate-traffic.sh http://localhost:3000 600
```

## Endpoints

| Endpoint            | Descripción                                        |
|---------------------|----------------------------------------------------|
| `GET /`             | Información de la API y lista de endpoints         |
| `GET /api/datos`    | Datos simulados, respuesta rápida                  |
| `GET /api/lento`    | Procesamiento lento simulado (2 a 3 s)             |
| `GET /api/error`    | Falla con 500 en ~30% de los casos (`ERROR_RATE`)  |
| `GET/POST /api/items` | Lista o crea items en memoria                    |
| `GET /api/calculo/<n>` | Cálculo que consume CPU                         |
| `GET /health`       | Estado de la API                                   |
| `GET /metrics`      | Métricas en formato Prometheus                     |

## Métricas expuestas

| Métrica | Tipo | Para qué sirve |
|---|---|---|
| `http_requests_total{method,endpoint,status}` | Counter | Requests totales, throughput y errores |
| `http_request_duration_seconds{method,endpoint}` | Histogram | Latencia: promedio, p95, p99 |
| `http_requests_in_progress{endpoint}` | Gauge | Requests activos |
| `system_cpu_percent`, `system_memory_percent` | Gauge | CPU y memoria del sistema |
| `api_process_memory_bytes` | Gauge | Memoria del proceso de la API |
| `api_items_creados_total` | Counter | Métrica de negocio personalizada |
| `process_*`, `python_gc_*` | Varios | Métricas por defecto de la librería |

## Queries PromQL de ejemplo

```promql
sum by (endpoint) (rate(http_requests_total[1m]))
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[1m])))
100 * sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))
```

## Dashboard

11 paneles: requests totales, throughput actual, tasa de errores, requests activos, throughput por endpoint, latencia (promedio/p95/p99), p95 por endpoint, requests por código de estado, activos por endpoint, memoria, y CPU/memoria del sistema.

## Alertas (Prometheus)

Definidas en `prometheus/alerts.yml` y visibles en http://localhost:9090/alerts:

- **APICaida:** la API no responde al scraping por 30 s.
- **TasaErroresAlta:** más del 20% de errores 5xx durante 1 minuto.
- **LatenciaP95Alta:** p95 mayor a 2 s durante 1 minuto.

## Logging

Cada request genera una línea JSON en stdout (método, endpoint, status, duración en ms):

```bash
docker-compose logs -f api
```

## Decisiones técnicas

- Gunicorn con **1 worker y 8 hilos**: `prometheus-client` guarda las métricas en memoria del proceso, con varios workers cada uno tendría contadores distintos.
- La etiqueta `endpoint` usa la ruta definida (`/api/calculo/<int:n>`) y no la URL real, para no disparar la cardinalidad de series.
- `/metrics` no se cuenta a sí mismo en las métricas de requests.

## Apagar

```bash
docker-compose down      # conserva datos
docker-compose down -v   # borra volúmenes
```
