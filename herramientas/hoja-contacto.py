"""Compone renders del turntable sobre el fondo real del hero, para juzgarlos.

    python3 herramientas/hoja-contacto.py /tmp/prueba /tmp/hoja.png [ancho]

POR QUÉ EXISTE. Los fotogramas salen con alfa y nunca se ven solos: van sobre
la fotografía del guadual de la portada, que es verde, oscura y de luz difusa.
Mirando el PNG contra el gris del visor de imágenes se juzga mal —todo parece
más claro y más contrastado de lo que será—, y así se tomaron un par de
decisiones de luz que luego no se sostuvieron en la página.

El fondo no es un verde inventado: es `assets/texturas/guadual-quebrada.jpg`,
la misma imagen que sirve el hero, con el mismo virado que le aplica el sitio
(ver `.guadual img` y `.tinte` en `VidaGuadual.astro`, y el filtro del hero).
"""
import sys, glob, os
from PIL import Image, ImageEnhance

FONDO = 'web/src/assets/texturas/guadual-quebrada.jpg'

entrada = sys.argv[1]
salida = sys.argv[2] if len(sys.argv) > 2 else '/tmp/hoja.png'
ancho_celda = int(sys.argv[3]) if len(sys.argv) > 3 else 520

rutas = sorted(glob.glob(os.path.join(entrada, '*.png')) +
               glob.glob(os.path.join(entrada, '*.webp')))
if not rutas:
    sys.exit(f'no hay renders en {entrada}')

# EL VELO ES EL DE LA PÁGINA, no un oscurecido a ojo. El hero tapa su
# fotografía con un degradado de `--bg` (#1D2316, el Negro Verde del manual)
# que va del 2 % de transparencia abajo al 25 % arriba; a la altura donde vive
# el modelo —mitad derecha, algo por encima del centro— lo que cae encima es
# del orden del 40 %. Ese es el número de aquí.
#
# Importa acertarlo: juzgando contra un fondo más claro que el real, un modelo
# demasiado oscuro parece correcto, y al revés. Ver `.lienzo::after` en
# `Hero.astro`.
BG = (0x1D, 0x23, 0x16)
VELO = 0.40

fondo = Image.open(FONDO).convert('RGB')
capa = Image.new('RGB', fondo.size, BG)
fondo = Image.blend(fondo, capa, VELO)

celdas = []
for r in rutas:
    im = Image.open(r).convert('RGBA')
    esc = ancho_celda / im.width
    im = im.resize((ancho_celda, max(1, round(im.height * esc))), Image.LANCZOS)
    # Un trozo distinto del fondo para cada celda: sobre un fondo uniforme, un
    # borde sucio o un halo pueden pasar desapercibidos justo en esa zona.
    caja = fondo.crop((0, 0, fondo.width, fondo.height)).resize(im.size, Image.LANCZOS)
    celdas.append((os.path.basename(r), Image.alpha_composite(caja.convert('RGBA'), im).convert('RGB')))

cols = min(2, len(celdas))
filas = (len(celdas) + cols - 1) // cols
w, h = celdas[0][1].size
hoja = Image.new('RGB', (w * cols, h * filas), (16, 18, 14))
for i, (_, im) in enumerate(celdas):
    hoja.paste(im, ((i % cols) * w, (i // cols) * h))
hoja.save(salida)
print(f'{len(celdas)} vistas · {hoja.size[0]}x{hoja.size[1]} · {salida}')
print('  ' + '  '.join(n for n, _ in celdas))
