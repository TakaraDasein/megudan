"""Quita el halo gris del borde de los fotogramas de croma.

    python3 herramientas/desflecar-360.py web/public/kiosco-paja-360

EL PROBLEMA. Los modelos que salen de un video con fondo verde
(`extraer-secuencia.sh` → `chromakey` + `despill`) llegan con los bordes
lavados. En un píxel de borde, el color grabado es mezcla de guadua y verde;
`despill` neutraliza ese verde, y neutralizar una mezcla no devuelve la guadua:
devuelve un gris claro. Medido sobre `paja-008`, el borde tenía saturación 0.18
contra 0.56 del interior, y un RGB de (201,185,167) contra (139,106,66). Sobre
el guadual —oscuro y verde— ese anillo claro se ve como escarcha alrededor de
las columnas.

LA CORRECCIÓN. No es una capa de color encima: eso teñiría también el interior,
que está bien. Es sangrar el color sólido hacia afuera —el «alpha bleed» de
toda la vida— y quedarse con el alfa original. Cada píxel de borde recibe el
color de la guadua que tiene al lado y conserva su transparencia, así que la
silueta y el antialiasing no cambian; lo único que cambia es de qué color es lo
que se desvanece.

El alfa NO SE TOCA. Erosionarlo un píxel también mata el halo, pero adelgaza
las columnas de la celosía, que aquí tienen tres o cuatro píxeles de ancho: se
volverían hilos y a ratos se cortarían. El color se puede mentir; la silueta no.
"""
import sys, glob, os
import numpy as np
from PIL import Image

SOLIDO = 250      # de aquí arriba, el píxel es color bueno y sirve de fuente
PASADAS = 6       # cuántos píxeles hacia afuera se sangra el color


def desflecar(arr):
    rgb = arr[..., :3].astype(np.float32)
    alfa = arr[..., 3]
    bueno = alfa >= SOLIDO

    # El color se propaga como una marea: en cada pasada, los píxeles que aún
    # no tienen color bueno toman la media de los vecinos que sí lo tienen, y
    # pasan a ser fuente para la pasada siguiente. Seis pasadas cubren de sobra
    # un borde de antialiasing, que rara vez pasa de dos o tres píxeles.
    color = rgb.copy()
    valido = bueno.copy()
    for _ in range(PASADAS):
        if valido.all():
            break
        suma = np.zeros_like(color)
        cuenta = np.zeros(alfa.shape, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                c = np.roll(np.roll(color, dy, 0), dx, 1)
                v = np.roll(np.roll(valido, dy, 0), dx, 1).astype(np.float32)
                suma += c * v[..., None]
                cuenta += v
        nuevos = (~valido) & (cuenta > 0)
        color[nuevos] = suma[nuevos] / cuenta[nuevos][..., None]
        valido |= nuevos

    salida = arr.copy()
    # Solo donde el píxel no era ya sólido: el interior se deja intacto.
    salida[..., :3] = np.where(bueno[..., None], arr[..., :3],
                               np.clip(color, 0, 255).astype(np.uint8))
    return salida


def satura(a):
    px = a[..., :3].astype(np.float32)
    mx, mn = px.max(-1), px.min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)


directorio = sys.argv[1]
calidad = int(sys.argv[2]) if len(sys.argv) > 2 else 82
rutas = sorted(glob.glob(os.path.join(directorio, '*.webp')))
if not rutas:
    sys.exit(f'no hay webp en {directorio}')

antes = despues = 0.0
for r in rutas:
    a = np.asarray(Image.open(r).convert('RGBA'))
    borde = (a[..., 3] > 16) & (a[..., 3] < 239)
    b = desflecar(a)
    if borde.any():
        antes += satura(a)[borde].mean()
        despues += satura(b)[borde].mean()
    Image.fromarray(b, 'RGBA').save(r, 'WEBP', quality=calidad, method=6)

n = len(rutas)
total = sum(os.path.getsize(x) for x in rutas) / 1024 / 1024
print(f'listo · {n} fotogramas · saturación del borde {antes/n:.3f} → {despues/n:.3f}'
      f' · {total:.2f} MB')
