#!/usr/bin/env python3
"""Variantes móviles de las secuencias: menos fotogramas y menos píxeles.

QUÉ RESUELVE. El descenso del guadual y sus kioscos existen solo en escritorio
porque pesan 10,6 MB entre todos —4,5 la secuencia y 6,1 los tres modelos—, y
eso en datos móviles, en la tercera sección de la portada, no se puede pedir.
Este script deriva de esas mismas fuentes un juego paralelo que cabe: mismas
imágenes, menos de las que hay y más pequeñas.

NO ES UNA FUENTE, ES UN DERIVADO. Lee de `web/public/` y escribe en
`web/public/`, siempre en una carpeta hermana con sufijo `-movil`. Si se
regenera la secuencia de origen —`extraer-secuencia.sh`, `render-kiosco-360.py`—
hay que volver a correr este script detrás, o el móvil se queda con la versión
anterior sin avisar de nada.

CÓMO SE ELIGEN LOS FOTOGRAMAS. Linealmente sobre los índices del origen, con los
DOS EXTREMOS INCLUIDOS. Eso importa por motivos distintos en cada secuencia:

· El guadual no es un bucle sino un descenso, y sus dos extremos son los dos
  planos con los que la sección abre y cierra —el dosel y el brote—. Perder
  cualquiera de los dos le quita a la sección su primer o su último fotograma.
  Y el reparto del origen ya es por MOVIMIENTO y no por tiempo (ver
  `extraer-secuencia.sh`), así que tomar uno de cada N conserva esa propiedad:
  el mapeo scroll→fotograma sigue siendo lineal por construcción.

· Los kioscos sí son un bucle de 360°, y ahí incluir los dos extremos significa
  quedarse con el primero y con el último de la vuelta, que están separados por
  un paso normal. Se toman los pares, que es lo mismo dicho de otra forma.

EL RECORTE A RETRATO ES SOLO DEL GUADUAL, y es la mitad del ahorro. El origen es
un vídeo 16:9 y en un móvil el lienzo lo pinta con `cover`: de 1280 px de ancho
se ven unos 400 y el resto se tira. Recortando el centro a 9:16 antes de
comprimir, cada byte que se descarga cae dentro de la pantalla. Se puede recortar
al centro porque el culmo protagonista está centrado en todo el descenso —
comprobado sobre los fotogramas 000, 024, 048 y 071—; si alguna vez se cambia el
vídeo de origen, esto hay que volver a mirarlo antes de confiar en el recorte.

Los kioscos NO se recortan: van sobre fondo transparente y su encuadre ya viene
ajustado a la silueta por `empacar-360.py`. Recortarlos otra vez sería morderles
el edificio.

CALIDAD 70, la misma que `empacar-360.py`, y por su mismo motivo: estas imágenes
llevan fibra y grano, que es ruido de alta frecuencia y el códec lo paga. La
medición está en la cabecera de aquel.

Uso:
    python3 herramientas/ligeras-movil.py            # todas
    python3 herramientas/ligeras-movil.py guadual    # solo una
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("hacen falta Pillow y NumPy:  pip install --user Pillow numpy")

RAIZ = Path(__file__).resolve().parent.parent
PUBLICO = RAIZ / "web" / "public"

CALIDAD = 70

# EL VIRADO DEL GUADUAL SE HORNEA AQUÍ, no se aplica en CSS.
#
# La misma cadena que llevaba `.guadual img, .guadual canvas` en
# `VidaGuadual.astro`, en el mismo orden. Se movió a este script porque medida
# contra un móvil de gama media resultó ser el coste dominante de la sección:
# el lienzo ocupa la pantalla entera y cambia de contenido en cada fotograma del
# scrub, así que un `filter` de CSS encima obliga al navegador a refiltrar
# 1,5 megapíxeles en cada uno. Medido en Chromium con la CPU al 25 %, sobre el
# build de producción y con el dedo emulado: el fotograma mediano pasa de
# 33,3 ms a 16,7 ms —de 30 a 60 fps— y los fotogramas de más de 50 ms caen del
# 14,6 % al 1,8 %. Dibujar la imagen cuesta 0,05 ms; volver a filtrarla, dieciséis.
#
# El póster SIGUE virándose por CSS y eso es correcto: es una imagen fija, se
# filtra una vez y no entra en el presupuesto de ningún fotograma. Por eso los
# dos tienen que dar el mismo color, y por eso esto replica la cadena en vez de
# inventar un virado nuevo.
#
# SI SE CAMBIA EL VIRADO, hay que cambiarlo en los dos sitios y volver a correr
# este script. No hay nada que avise: en escritorio el lienzo se sigue virando
# por CSS y se ve bien.
VIRADO = dict(contraste=1.16, saturacion=1.05, brillo=0.84, giro_tono=-4.0)

# Cada trabajo: de dónde lee, a dónde escribe, cuántos fotogramas deja y a qué
# ancho.
#
# LOS ANCHOS SALEN DE LO QUE LA PANTALLA ENSEÑA, no de una fracción del origen.
# El guadual ocupa la sección entera: en un móvil de 390 px CSS con dpr 2 son
# 780 px reales, y 540 es el punto donde el escalado todavía no se ve sobre una
# fotografía con tanto grano —el ojo lo lee como profundidad de campo, no como
# falta de resolución—. Los kioscos van en miniatura al pie de la frase, unos
# 200 px CSS, así que 420 los cubre con dpr 2 de sobra.
TRABAJOS = {
    "guadual": {
        "origen": PUBLICO / "secuencia",
        "patron": "guadual-*.webp",
        "destino": PUBLICO / "secuencia-movil",
        "prefijo": "guadual-",
        "cuantos": 18,
        "ancho": 540,
        "retrato": True,
        "virado": VIRADO,
    },
    "sumak-calido": {
        "origen": PUBLICO / "modelo-360-calido",
        "patron": "modelo-*.webp",
        "destino": PUBLICO / "modelo-360-calido-movil",
        "prefijo": "modelo-",
        "cuantos": 18,
        "ancho": 420,
        "retrato": False,
    },
    "teja": {
        "origen": PUBLICO / "kiosco-teja-360",
        "patron": "teja-*.webp",
        "destino": PUBLICO / "kiosco-teja-360-movil",
        "prefijo": "teja-",
        "cuantos": 18,
        "ancho": 420,
        "retrato": False,
    },
    "paja": {
        "origen": PUBLICO / "kiosco-paja-360",
        "patron": "paja-*.webp",
        "destino": PUBLICO / "kiosco-paja-360-movil",
        "prefijo": "paja-",
        "cuantos": 18,
        "ancho": 420,
        "retrato": False,
    },
}

# 9:16, la proporción de un móvil de pie. No se toma de la ventana real porque
# el lienzo hace `cover`: basta con que la fuente sea al menos tan estrecha como
# la pantalla más estrecha que la vaya a enseñar.
RETRATO = 9 / 16




def virar(im: Image.Image, contraste: float, saturacion: float,
          brillo: float, giro_tono: float) -> Image.Image:
    """La cadena `filter` de CSS, en sRGB y en el mismo orden que la declara.

    Cada función de la abreviatura es una primitiva independiente y el
    resultado se acota entre primitivas, así que se acota en cada paso: hacerlo
    solo al final daría un color distinto en las zonas que se pasan de rango.
    """
    modo = im.mode
    rgb = np.asarray(im.convert("RGBA" if modo == "RGBA" else "RGB"),
                     dtype=np.float32) / 255.0
    alfa = rgb[..., 3:] if modo == "RGBA" else None
    v = rgb[..., :3]

    v = np.clip(v * contraste + (0.5 - 0.5 * contraste), 0.0, 1.0)

    s = saturacion
    m_sat = np.array([
        [0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s],
        [0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s],
        [0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s],
    ], dtype=np.float32)
    v = np.clip(v @ m_sat.T, 0.0, 1.0)

    v = np.clip(v * brillo, 0.0, 1.0)

    a = np.radians(giro_tono)
    c, n = np.cos(a), np.sin(a)
    m_tono = np.array([
        [0.213 + c * 0.787 - n * 0.213, 0.715 - c * 0.715 - n * 0.715, 0.072 - c * 0.072 + n * 0.928],
        [0.213 - c * 0.213 + n * 0.143, 0.715 + c * 0.285 + n * 0.140, 0.072 - c * 0.072 - n * 0.283],
        [0.213 - c * 0.213 - n * 0.787, 0.715 - c * 0.715 + n * 0.715, 0.072 + c * 0.928 + n * 0.072],
    ], dtype=np.float32)
    v = np.clip(v @ m_tono.T, 0.0, 1.0)

    salida = v if alfa is None else np.concatenate([v, alfa], axis=-1)
    return Image.fromarray((salida * 255.0 + 0.5).astype(np.uint8), modo if modo in ("RGB", "RGBA") else "RGB")


def elegidos(total: int, cuantos: int) -> list[int]:
    """`cuantos` índices repartidos por igual, con el primero y el último dentro."""
    if cuantos >= total:
        return list(range(total))
    return [round(k * (total - 1) / (cuantos - 1)) for k in range(cuantos)]


def recorte_retrato(im: Image.Image) -> Image.Image:
    """La franja central de proporción 9:16. Ver la nota de la cabecera."""
    ancho_util = round(im.height * RETRATO)
    if ancho_util >= im.width:
        return im
    izq = (im.width - ancho_util) // 2
    return im.crop((izq, 0, izq + ancho_util, im.height))


def derivar(nombre: str, t: dict) -> None:
    fuentes = sorted(t["origen"].glob(t["patron"]))
    if not fuentes:
        sys.exit(f"· {nombre}: no hay fotogramas en {t['origen'].relative_to(RAIZ)}")

    destino: Path = t["destino"]
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in destino.glob(t["patron"]):
        viejo.unlink()

    indices = elegidos(len(fuentes), t["cuantos"])
    for k, i in enumerate(indices):
        im = Image.open(fuentes[i])
        if t["retrato"]:
            im = recorte_retrato(im)
        if t.get("virado"):
            im = virar(im, **t["virado"])
        alto = round(im.height * t["ancho"] / im.width)
        im = im.resize((t["ancho"], alto), Image.LANCZOS)
        salida = destino / f"{t['prefijo']}{k:03d}.webp"
        # `lossless=False` explícito: con RGBA, Pillow elige sin pérdida por su
        # cuenta y una miniatura del kiosco se va a 120 KB, más que el original.
        im.save(salida, "WEBP", quality=CALIDAD, method=6, lossless=False)

    antes = sum(f.stat().st_size for f in fuentes)
    ahora = sum(f.stat().st_size for f in destino.glob(t["patron"]))
    primera = Image.open(sorted(destino.glob(t["patron"]))[0])
    print(
        f"· {nombre:14} {len(fuentes):2}→{len(indices):2} fot  "
        f"{primera.size[0]}x{primera.size[1]}  "
        f"{antes / 1e6:5.2f}→{ahora / 1e6:4.2f} MB  "
        f"({ahora / antes:.0%})"
    )


def main() -> None:
    pedidos = sys.argv[1:] or list(TRABAJOS)
    desconocidos = [p for p in pedidos if p not in TRABAJOS]
    if desconocidos:
        sys.exit(f"no conozco: {', '.join(desconocidos)}\nhay: {', '.join(TRABAJOS)}")

    total_antes = total_ahora = 0
    for nombre in pedidos:
        derivar(nombre, TRABAJOS[nombre])
        t = TRABAJOS[nombre]
        total_antes += sum(f.stat().st_size for f in t["origen"].glob(t["patron"]))
        total_ahora += sum(f.stat().st_size for f in t["destino"].glob(t["patron"]))

    print(f"\n  total móvil: {total_ahora / 1e6:.2f} MB "
          f"(de {total_antes / 1e6:.2f} MB en escritorio)")


if __name__ == "__main__":
    main()
