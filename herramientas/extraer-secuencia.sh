#!/usr/bin/env bash
# Extrae los fotogramas del guadual para el hero.
#
# No los reparte por tiempo sino por MOVIMIENTO. El video tiene casi dos
# segundos muertos al principio y luego acelera; si se extrajera cada N
# fotogramas, el visitante scrollearía un cuarto de la sección para ver un 3 %
# del crecimiento. Repartiendo por movimiento acumulado, cada fotograma aporta
# el mismo cambio visual y el mapeo scroll→fotograma vuelve a ser lineal.
set -euo pipefail

VIDEO="${1:-fuentes-video/guadual.mp4}"
SALIDA="${2:-web/public/secuencia}"
TOTAL="${3:-72}"
# El video es de 1280 px de ancho: escalarlo hacia arriba no añade detalle,
# solo peso. Se extrae a resolución nativa y el CSS lo estira.
CALIDAD=72

command -v ffmpeg >/dev/null || { echo "hace falta ffmpeg"; exit 1; }

echo "1/3 · midiendo el movimiento del video…"
ffmpeg -hide_banner -i "$VIDEO" \
  -vf "scale=160:90,tblend=all_mode=difference,signalstats,metadata=print" \
  -an -f null - 2>&1 | grep -oE 'YAVG=[0-9.]+' | cut -d= -f2 > /tmp/mov.txt

echo "2/3 · eligiendo $TOTAL fotogramas repartidos por movimiento…"
python3 - "$TOTAL" > /tmp/tiempos.txt <<'PY'
import sys
total = int(sys.argv[1])
v = [float(x) for x in open('/tmp/mov.txt')]
suma = sum(v)
acum, tabla = 0.0, []
for x in v:
    acum += x
    tabla.append(acum / suma)
for k in range(total):
    objetivo = k / (total - 1)
    i = next((j for j, c in enumerate(tabla) if c >= objetivo - 1e-9), len(tabla) - 1)
    print(f"{i / 24:.4f}")   # 24 fps
PY

echo "3/3 · extrayendo a resolución nativa…"
rm -f "$SALIDA"/guadual-*.webp
k=0
while read -r t; do
  ffmpeg -v error -ss "$t" -i "$VIDEO" -frames:v 1 -an \
    -c:v libwebp -quality "$CALIDAD" -compression_level 6 \
    "$(printf '%s/guadual-%03d.webp' "$SALIDA" "$k")" -y
  k=$((k+1))
done < /tmp/tiempos.txt

echo
echo "listo: $(ls "$SALIDA"/guadual-*.webp | wc -l) fotogramas · $(du -sh "$SALIDA" | cut -f1)"
