"""Deja los fotogramas del turntable como los quiere el visor de la portada.

    python3 herramientas/empacar-360.py /tmp/kiosco-360 web/public/modelo-360

Entra un directorio de PNG RGBA recién salidos de `render-kiosco-360.py` y sale
`modelo-000.webp` … `modelo-035.webp`, que es lo que busca el `import.meta.glob`
de `Giratorio.astro`.

DOS COSAS QUE NO SON OBVIAS, las mismas que aprendió `extraer-modelo-360.sh` y
por la misma razón —el visor dibuja imágenes sueltas en un canvas, no un video—:

1. TODOS SE RECORTAN AL MISMO ENCUADRE, la unión de las 36 cajas, nunca cada uno
   a la suya. Recortando individualmente el kiosco cambiaría de tamaño en cada
   paso del arrastre: como es más ancho de frente que de esquina, su caja propia
   late, y al estirar cada fotograma a la misma casilla el edificio parecería
   respirar.
2. No se reescala hacia abajo. El remuestreo mete ringing de alta frecuencia y
   webp lo paga en bytes, así que el recorte nativo pesa menos que el mismo
   fotograma reducido y tiene más detalle. El lienzo pide del orden de 900 px
   reales en una pantalla de dpr 2.

Y la calidad por omisión es 70 Y NO 82, que es lo que se usa en el resto del
sitio. La razón es la cubierta: desde que la paja tiene fibra de verdad, el
fotograma es ruido de alta frecuencia, y eso es justo lo que un códec con
pérdida no puede tirar barato. Medido sobre estos mismos 36 fotogramas:

    q=82 → 4.05 MB    q=76 → 3.31 MB    q=70 → 3.04 MB    q=64 → 2.87 MB

La rodilla está en 70: de 82 a 76 se va el 18 %, de 76 a 70 el 8 %, y de ahí
para abajo el 6 %. Comparando recortes al 100 % de la cubierta, las cuatro son
indistinguibles —las hiladas aguantan hasta 64—, y encima el lienzo las dibuja
reducidas desde 1257 px. No se baja de 70 porque los 170 KB que quedan no pagan
el margen que se pierde.

REALISMO Y PESO SON LA MISMA VARIABLE. Si algún día se retoca el material de la
paja hacia más detalle, esto sube otra vez: el render liso de antes pesaba 1.96
MB precisamente porque era liso. La secuencia entra por `requestIdleCallback`
para no competir con la fotografía del hero, que es la que mide el LCP, pero el
presupuesto de la portada es el que documenta CLAUDE.md y no es infinito.
"""
import sys, glob, os
from PIL import Image

entrada = sys.argv[1] if len(sys.argv) > 1 else '/tmp/kiosco-360'
salida = sys.argv[2] if len(sys.argv) > 2 else 'web/public/modelo-360'
calidad = int(sys.argv[3]) if len(sys.argv) > 3 else 70
margen = 12

rutas = sorted(glob.glob(os.path.join(entrada, 'bruto-*.png')))
if not rutas:
    sys.exit(f'no hay bruto-*.png en {entrada}')
imgs = [Image.open(r).convert('RGBA') for r in rutas]

cajas = [im.split()[3].getbbox() for im in imgs]
x0 = max(0, min(c[0] for c in cajas) - margen)
y0 = max(0, min(c[1] for c in cajas) - margen)
x1 = min(imgs[0].width, max(c[2] for c in cajas) + margen)
y1 = min(imgs[0].height, max(c[3] for c in cajas) + margen)
print(f'· encuadre común {x1-x0}×{y1-y0}  (relación {(x1-x0)/(y1-y0):.3f})')

os.makedirs(salida, exist_ok=True)
for viejo in glob.glob(os.path.join(salida, 'modelo-*.webp')):
    os.remove(viejo)

total = 0
for i, im in enumerate(imgs):
    destino = os.path.join(salida, f'modelo-{i:03d}.webp')
    im.crop((x0, y0, x1, y1)).save(destino, 'WEBP', quality=calidad, method=6)
    total += os.path.getsize(destino)
print(f'listo · {len(imgs)} fotogramas, {total/1024/1024:.2f} MB en {salida}')
