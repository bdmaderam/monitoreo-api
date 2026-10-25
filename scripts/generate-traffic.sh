#!/usr/bin/env bash
# Tráfico sintético con curl. Uso: ./scripts/generate-traffic.sh [URL] [SEGUNDOS]
BASE="${1:-http://localhost:3000}"
DURACION="${2:-600}"
FIN=$((SECONDS + DURACION))
RUTAS=("/" "/api/datos" "/api/datos" "/api/datos" "/api/items" "/api/lento" "/api/error" "/api/error" "/api/calculo/150000" "/health" "/no-existe")
echo "Generando tráfico a $BASE durante ${DURACION}s (Ctrl+C para parar)"
while [ $SECONDS -lt $FIN ]; do
  R=${RUTAS[$RANDOM % ${#RUTAS[@]}]}
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$R")
  echo "$(date +%T) GET $R -> $CODE"
  sleep 0.$((RANDOM % 5 + 1))
done
