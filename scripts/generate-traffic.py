"""Genera tráfico sintético hacia la API. Solo usa la librería estándar.
Uso: python scripts/generate-traffic.py [URL] [SEGUNDOS]
"""
import random
import sys
import threading
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
DURACION = int(sys.argv[2]) if len(sys.argv) > 2 else 600
HILOS = 6

# (método, ruta, peso)
RUTAS = [
    ("GET", "/", 10),
    ("GET", "/api/datos", 35),
    ("GET", "/api/items", 15),
    ("POST", "/api/items", 5),
    ("GET", "/api/lento", 8),
    ("GET", "/api/error", 15),
    ("GET", "/api/calculo/150000", 7),
    ("GET", "/health", 5),
    ("GET", "/ruta-que-no-existe", 2),
]
pesos = [r[2] for r in RUTAS]
total = 0
lock = threading.Lock()


def worker(fin):
    global total
    while time.time() < fin:
        metodo, ruta, _ = random.choices(RUTAS, weights=pesos)[0]
        req = urllib.request.Request(BASE + ruta, method=metodo,
                                     data=b"{}" if metodo == "POST" else None)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                codigo = r.status
        except urllib.error.HTTPError as e:
            codigo = e.code
        except Exception as e:
            codigo = f"ERR {e}"
        with lock:
            total += 1
            if total % 25 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] {total} requests (último: {metodo} {ruta} -> {codigo})")
        time.sleep(random.uniform(0.05, 0.6))


if __name__ == "__main__":
    print(f"Generando tráfico a {BASE} durante {DURACION}s con {HILOS} hilos. Ctrl+C para parar.")
    fin = time.time() + DURACION
    hilos = [threading.Thread(target=worker, args=(fin,), daemon=True) for _ in range(HILOS)]
    for h in hilos:
        h.start()
    try:
        while time.time() < fin:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    print(f"Listo. Total de requests enviados: {total}")
