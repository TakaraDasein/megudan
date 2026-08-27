#!/usr/bin/env bash
# Convierte un video de turntable en los fotogramas que consume el visor.
#
# El visor (`components/Giratorio.astro` + `giratorioArrastre` en motion.ts) no
# reproduce video: dibuja imágenes numeradas en un canvas. Este script hace el
# camino entero.
#
# Tres cosas que no son obvias:
#
# 1. El croma del video no es verde de plató (#00B140) sino un verde apagado
#    (#60AA5B). `chromakey` trabaja en YUV y con ese verde la tolerancia buena
#    es estrecha: por encima de 0.10 se empieza a comer la guadua, y por debajo
#    de 0.05 sobrevive la marca de agua en forma de destello. 0.06 es el punto.
# 2. Todos los fotogramas se recortan al MISMO encuadre —la unión de las cajas
#    de los 36—, no cada uno al suyo. Recortando individualmente el modelo
#    saltaría de tamaño en cada paso del arrastre.
# 3. `ffmpeg` numera desde 001 y el visor espera desde 000. Se renumera al final.
set -euo pipefail

VIDEO="${1:-fuentes-video/kiosco-360.mp4}"
SALIDA="${2:-web/public/modelo-360}"
TOTAL="${3:-36}"
CROMA="${4:-0x60AA5B}"
# Tramo del video que se usa, en segundos. El primer kiosco generado no orbita:
# oscila, y solo el tramo 1.58 s – 5.17 s es un barrido monótono, sin
# devolverse. Tomar el video entero mete un cambio de sentido en mitad de la
# secuencia y el arrastre se ve como un temblor. Con un turntable de verdad
# esto se pone a 0 y a la duración completa.
DESDE="${5:-1.583}"
HASTA="${6:-5.167}"
# 0 = tamaño nativo del recorte. Reescalar hacia abajo no ahorra: el remuestreo
# añade ringing de alta frecuencia que webp paga en bytes, así que el nativo
# (995 px) pesa MENOS que el mismo fotograma reducido a 780 y tiene 27 % más
# detalle. Además el lienzo pide 926 px reales en una pantalla dpr 2: por
# debajo de eso el modelo se amplía y se ve sucio.
ANCHO="${7:-0}"
CALIDAD="${8:-82}"

command -v ffmpeg >/dev/null || { echo "hace falta ffmpeg"; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

TRAMO=$(python3 -c "print(f'{$HASTA - $DESDE:.4f}')")

echo "1/3 · sacando $TOTAL fotogramas de ${DESDE}s a ${HASTA}s y quitando el croma…"
ffmpeg -v error -ss "$DESDE" -to "$HASTA" -i "$VIDEO" \
  -vf "fps=$TOTAL/$TRAMO,chromakey=$CROMA:0.06:0.04,despill=type=green:mix=0.5:expand=0.2" \
  -frames:v "$TOTAL" "$TMP/bruto-%03d.png" -y

echo "2/3 · recortando los $TOTAL al mismo encuadre…"
python3 - "$TMP" "$ANCHO" <<'PY'
import sys, glob, os
from PIL import Image

tmp, ancho = sys.argv[1], int(sys.argv[2])
rutas = sorted(glob.glob(os.path.join(tmp, 'bruto-*.png')))
imgs = [Image.open(r).convert('RGBA') for r in rutas]

# Unión de las cajas: el encuadre tiene que servir para todos o el modelo
# cambia de tamaño entre fotogramas y el arrastre se ve a saltos.
cajas = [im.split()[3].getbbox() for im in imgs]
x0 = min(c[0] for c in cajas); y0 = min(c[1] for c in cajas)
x1 = max(c[2] for c in cajas); y1 = max(c[3] for c in cajas)
margen = 12
x0, y0 = max(0, x0 - margen), max(0, y0 - margen)
x1, y1 = min(imgs[0].width, x1 + margen), min(imgs[0].height, y1 + margen)
print(f'    encuadre {x1-x0}×{y1-y0}  (relación {(x1-x0)/(y1-y0):.3f})')

for i, im in enumerate(imgs):
    rec = im.crop((x0, y0, x1, y1))
    if ancho and ancho != rec.width:
        rec = rec.resize((ancho, round(ancho * rec.height / rec.width)), Image.LANCZOS)
    rec.save(os.path.join(tmp, f'listo-{i:03d}.png'))
PY

echo "3/3 · pasando a webp con alfa…"
mkdir -p "$SALIDA"
rm -f "$SALIDA"/modelo-*.webp
for f in "$TMP"/listo-*.png; do
  n="${f##*/listo-}"; n="${n%.png}"
  ffmpeg -v error -i "$f" -c:v libwebp -quality "$CALIDAD" -compression_level 6 \
    "$SALIDA/modelo-$n.webp" -y
done

echo "listo · $(ls "$SALIDA"/modelo-*.webp | wc -l) fotogramas, $(du -sh "$SALIDA" | cut -f1) en total"
