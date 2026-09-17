#!/usr/bin/env python3
"""Recorta el culmo protagonista del descenso, fotograma a fotograma.

QUÉ PRODUCE
-----------
Una secuencia WebP con alfa donde solo queda el sujeto que la cámara sigue —el
culmo maduro arriba, el brote abajo— sobre fondo transparente. Sale en
`modelos-3d/secuencias/culmo/<version>/` y NO toca `web/public/secuencia/`:
aquello es lo que el sitio sirve hoy y esto es una versión nueva del taller.

PARA QUÉ
--------
El descenso del guadual no puede tener paralaje de verdad porque el sujeto está
horneado en la fotografía: mover el fondo mueve también la caña. Con esta capa
separada sí se puede — el fondo por un lado, el culmo por otro, a velocidades
distintas.

CÓMO SEGMENTA, Y HASTA DÓNDE LLEGA
----------------------------------
Dos motores, y el que manda es `rembg`.

`rembg` (U²-Net) SEGMENTA POR SEMÁNTICA y es lo único que resuelve esto. El
brote y la hojarasca son el mismo marrón, a la misma distancia y con la misma
luz: no hay color, ni foco, ni forma que los separe. Lo que hace falta no es
información cromática sino saber que eso es un brote y aquello es suelo. Medido
contra GrabCut en el fotograma 12: GrabCut se llevaba pegotes de hojarasca a los
dos lados; `rembg` devuelve la silueta con sus vainas.

PERO FALLA DE GOLPE, no degradando, y eso obliga a la guarda de continuidad de
más abajo. En el fotograma 18 devuelve un jirón del 1,6 % —perdió el sujeto—, y
un fotograma sin sujeto en mitad de la secuencia es un parpadeo.

`grabcut` es el respaldo, y queda porque no depende de nada: GrabCut sembrado y
propagado en el tiempo. Sirve para trabajar sin el modelo instalado, no para
publicar.

  1. El PRIMER fotograma se siembra con un rectángulo en la banda central. Se
     empieza por el 0 —el brote— y no por el 71 a propósito: el brote es marrón
     sobre hojarasca oscura y está enfocado contra un fondo desenfocado, o sea
     el fotograma donde el sujeto se separa mejor. Sembrar por el lado fácil y
     propagar hacia el difícil es lo único que da alguna oportunidad arriba.
  2. Cada fotograma siguiente se siembra con la máscara del anterior: erosionada
     es «seguro sujeto», dilatada es «probable sujeto», y todo lo que quede
     fuera de la banda central es «seguro fondo». La cámara se mueve poco entre
     fotogramas contiguos, así que el solape es alto.
  3. Se queda la componente conexa que toca la columna central, para que un
     jirón de hojarasca suelto no entre en la capa.
  4. El alfa se suaviza con un desenfoque corto: un filo duro recortado sobre
     una fotografía se ve más que el propio recorte.

LO QUE NO RESUELVE, y hay que saberlo antes de usarlo
-----------------------------------------------------
Cuanto más arriba, peor, y con los dos motores.

Con `rembg` el sujeto deja de ser un objeto: abajo es UN BROTE —una cosa
entera, con su forma— y arriba es un tramo de caña que entra y sale del
encuadre. U²-Net busca el objeto saliente, así que cuando ya no hay objeto sino
trozo, devuelve el segmento que le parece y lo corta por donde quiere. Ahí la
máscara es correcta pero el recorte se ve amputado.

Con `grabcut`, además, en el dosel el culmo protagonista es UNO MÁS entre veinte
iguales: mismo color, mismo foco, mismo grosor, y la máscara acaba conteniendo
una columna de bosque.

Ninguno de los dos es un fallo de parámetros. Por eso la guarda decide sola
hasta dónde se publica, en vez de dejarlo a un número escrito a mano que
envejece con el vídeo de origen.

Por eso el script escribe además una HOJA DE CONTACTO: la idea es mirarla antes
de dar por buena la secuencia, no confiar en que 72 salieron bien porque tres lo
hicieron.

USO
---
    python3 herramientas/recortar-culmo.py            # versión v1, los 72
    python3 herramientas/recortar-culmo.py --version v2 --hasta 40
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

try:
    from rembg import new_session, remove

    HAY_REMBG = True
except ImportError:  # pragma: no cover
    HAY_REMBG = False

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "web/public/secuencia"
DESTINO = RAIZ / "modelos-3d/secuencias/culmo"

# LA BANDA DONDE PUEDE ESTAR EL SUJETO, en fracción de ancho. El culmo
# protagonista está centrado en todo el descenso —es el mismo hecho que permite
# recortar la secuencia a retrato para móvil— así que fuera de aquí no hay nada
# que buscar, y acotarlo le quita a GrabCut la tentación de irse a un vecino.
BANDA = (0.38, 0.62)

# Cuánto se abre y se cierra la máscara del fotograma anterior para sembrar el
# siguiente. La erosión marca lo que se da por seguro; la dilatación, hasta
# dónde se le permite crecer. Con la cámara moviéndose despacio, 12 px de margen
# cubren el desplazamiento entre contiguos sin dejarle sitio para saltar a otra
# caña.
SEGURO = 10
MARGEN = 12


# LA GUARDA DE CONTINUIDAD, que es la que decide hasta dónde se publica.
#
# Dos condiciones, y las dos contra el fotograma anterior aceptado:
#
#   · LA COBERTURA no puede saltar. La cámara se mueve despacio, así que el
#     tamaño del sujeto cambia poco entre contiguos; un salto grande significa
#     que la máscara cogió otra cosa —o dejó de coger nada—.
#   · Y TIENEN QUE SOLAPARSE. Dos máscaras del mismo sujeto en fotogramas
#     vecinos comparten casi toda su área. Una que no solapa es otro objeto,
#     aunque mida parecido: es el caso que la cobertura sola no pilla.
#
# Se comprueba contra el ANTERIOR ACEPTADO y no contra el inmediatamente
# anterior, porque si no un fallo aislado movería la referencia y arrastraría a
# los siguientes.
SALTO = 0.45
SOLAPE = 0.35


def continua(m, previa):
    if previa is None:
        return True
    a, b = m.mean() / 255, previa.mean() / 255
    if not b or abs(a - b) / b > SALTO:
        return False
    inter = np.logical_and(m > 0, previa > 0).sum()
    union = np.logical_or(m > 0, previa > 0).sum()
    return bool(union) and inter / union >= SOLAPE


def segmentar_rembg(rgb, sesion):
    """U²-Net sobre el fotograma entero, y luego la componente central.

    Se le pasa el marco COMPLETO y no la banda central, aunque el sujeto esté
    siempre ahí: el modelo decide qué es saliente comparando con todo lo que hay
    alrededor, y recortando antes se le quita justo el contexto con el que
    compara. Acotar viene después, con la componente conexa.
    """
    from PIL import Image as _Image

    salida = remove(_Image.fromarray(rgb), session=sesion)
    alfa = np.array(salida)[:, :, 3]

    # UMBRAL BAJO (40) Y SIN APERTURA MORFOLÓGICA, y las dos cosas son por LAS
    # PÚAS.
    #
    # Las hojas que salen del brote son finas y en contraluz, así que U²-Net las
    # devuelve semitransparentes: con el umbral en 110 se descartaban antes de
    # empezar. Y una apertura BORRA TODO LO MÁS FINO QUE SU NÚCLEO por
    # definición, así que un 5x5 se llevaba por delante justo lo que
    # caracteriza a un brote de guadua. El resultado era un cono liso, sin las
    # púas — reconocible pero no el mismo objeto.
    #
    # Lo que la apertura hacía de útil —tirar motas sueltas— ya lo hace
    # `mayor_central`, y lo hace mejor: descarta por conectividad, no por
    # grosor, así que una púa pegada al cuerpo se queda y una mota suelta se va.
    nucleo = mayor_central((alfa > 40).astype(np.uint8) * 255, rgb.shape[1])
    if not nucleo.any():
        return nucleo

    # Y SE DEVUELVE EL ALFA BLANDO, no la máscara binaria. Es la otra mitad: en
    # el borde de una púa no hay un sí o un no, hay un píxel medio hoja y medio
    # fondo. Binarizarlo y luego desenfocarlo —que es lo que se hacía— inventa
    # una transición donde el modelo ya daba la buena. Se recorta a la región
    # aceptada, dilatada con holgura para no morder las púas que asoman.
    permitido = cv2.dilate(nucleo, np.ones((25, 25), np.uint8))
    return np.where(permitido > 0, alfa, 0).astype(np.uint8)


def banda_px(w):
    return int(w * BANDA[0]), int(w * BANDA[1])


def mayor_central(m, w):
    """La componente conexa que toca la columna central; el resto se descarta."""
    num, lab, _, _ = cv2.connectedComponentsWithStats(m, 8)
    if num <= 1:
        return m
    centro = lab[:, int(w * 0.46) : int(w * 0.54)]
    mejor, area = 0, 0
    for i in range(1, num):
        a = int((centro == i).sum())
        if a > area:
            mejor, area = i, a
    if not mejor:
        return np.zeros_like(m)
    return np.where(lab == mejor, 255, 0).astype(np.uint8)


def segmentar(im, previa):
    h, w = im.shape[:2]
    x0, x1 = banda_px(w)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)

    if previa is None:
        mask = np.zeros((h, w), np.uint8)
        rect = (x0, int(h * 0.05), x1 - x0, int(h * 0.92))
        cv2.grabCut(im, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    else:
        nuc = np.ones((SEGURO * 2 + 1, SEGURO * 2 + 1), np.uint8)
        nud = np.ones((MARGEN * 2 + 1, MARGEN * 2 + 1), np.uint8)
        seguro = cv2.erode(previa, nuc)
        probable = cv2.dilate(previa, nud)

        mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
        mask[probable > 0] = cv2.GC_PR_FGD
        mask[seguro > 0] = cv2.GC_FGD
        # Fuera de la banda no hay sujeto posible, y decirlo explícitamente es
        # lo que impide que la máscara se escape a una caña vecina.
        mask[:, :x0] = cv2.GC_BGD
        mask[:, x1:] = cv2.GC_BGD
        cv2.grabCut(im, mask, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)

    m = np.where((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD), 0, 255).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return mayor_central(m, w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1")
    ap.add_argument(
        "--motor",
        choices=("rembg", "grabcut"),
        default="rembg" if HAY_REMBG else "grabcut",
        help="rembg segmenta por semántica; grabcut es el respaldo sin dependencias",
    )
    ap.add_argument("--hasta", type=int, default=None, help="corta antes, para probar")
    ap.add_argument("--calidad", type=int, default=82)
    ap.add_argument(
        "--publicar",
        type=int,
        default=0,
        metavar="N",
        help="además, deja los N primeros recortados en web/public/culmo/",
    )
    ap.add_argument(
        "--calidad-publicada",
        type=int,
        default=70,
        help="más agresiva que la del archivo: 70, como `empacar-360.py`",
    )
    ap.add_argument(
        "--solo-publicar",
        action="store_true",
        help="publica desde una versión ya hecha, sin volver a segmentar",
    )
    args = ap.parse_args()

    marcos = sorted(ORIGEN.glob("guadual-*.webp"))
    if args.hasta:
        marcos = marcos[: args.hasta]
    if not marcos:
        raise SystemExit(f"no hay fotogramas en {ORIGEN}")

    salida = DESTINO / args.version

    # PUBLICAR NO ES SEGMENTAR, y separarlo importa: la segmentación son 72
    # GrabCut y tarda, mientras que republicar es recortar y volver a comprimir.
    # Al afinar el peso o la calidad no hay por qué rehacer las máscaras — y
    # rehacerlas obligaría a inventar una versión nueva cada vez, que es
    # justamente lo que el archivo no quiere.
    if args.solo_publicar:
        if not salida.exists():
            raise SystemExit(f"no existe {salida}")
        publicar(salida, args.publicar or len(list(salida.glob("culmo-*.webp"))),
                 args.calidad_publicada)
        return

    if salida.exists() and any(salida.iterdir()):
        raise SystemExit(
            f"{salida} ya tiene contenido.\n"
            "Las versiones no se pisan: usa --version con un nombre nuevo.\n"
            "Durante el desarrollo del kiosco se perdieron un par de secuencias "
            "por renderizar encima, y sin la anterior no hay forma de saber si "
            "un cambio mejoró algo o solo lo cambió."
        )
    salida.mkdir(parents=True, exist_ok=True)

    if args.motor == "rembg" and not HAY_REMBG:
        raise SystemExit("falta `rembg`: pip install rembg onnxruntime")
    sesion = new_session("u2net") if args.motor == "rembg" else None

    previa = None
    fiables = 0
    corte = None
    hoja = []
    for i, ruta in enumerate(marcos):
        rgb = np.array(Image.open(ruta).convert("RGB"))
        if sesion is not None:
            m = segmentar_rembg(rgb, sesion)
        else:
            m = segmentar(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), previa)

        # El tramo fiable es un PREFIJO: en cuanto uno se rompe, se deja de
        # contar. No se reanuda aunque los siguientes vuelvan a salir bien,
        # porque lo que se publica tiene que ser una secuencia continua — un
        # hueco en medio se ve como un parpadeo, y arreglarlo pidiendo que los
        # de después "también valgan" es justo lo que no se puede comprobar.
        if corte is None:
            if continua(m, previa):
                fiables = i + 1
                previa = m
            else:
                corte = i
        
        # EL FILO. GrabCut devuelve una máscara binaria y hay que suavizarla —un
        # recorte duro sobre una fotografía se ve más que el propio recorte—,
        # pero el alfa de `rembg` YA VIENE BLANDO y con la transición en el sitio
        # correcto. Desenfocarlo otra vez sería emborronar las púas, que es
        # justo lo que se acaba de rescatar.
        alfa = m if sesion is not None else cv2.GaussianBlur(m, (5, 5), 0)
        Image.fromarray(np.dstack([rgb, alfa])).save(
            salida / f"culmo-{i:03d}.webp", quality=args.calidad, lossless=False
        )
        cob = 100 * m.mean() / 255
        if i % 12 == 0 or i == len(marcos) - 1:
            hoja.append((i, rgb, alfa))
        print(f"· culmo-{i:03d}  cobertura {cob:4.1f} %")

    # LA HOJA DE CONTACTO, sobre magenta: es el fondo que menos se parece a nada
    # de esta escena, así que cualquier jirón de hojarasca que se haya colado
    # salta a la vista. Mirarla es parte del trabajo, no un extra.
    if hoja:
        w, h = hoja[0][1].shape[1] // 3, hoja[0][1].shape[0] // 3
        lienzo = Image.new("RGB", (w * len(hoja), h), (120, 20, 90))
        for j, (i, rgb, alfa) in enumerate(hoja):
            pieza = Image.fromarray(np.dstack([rgb, alfa])).resize((w, h))
            celda = Image.new("RGB", (w, h), (120, 20, 90))
            celda.paste(pieza, (0, 0), pieza)
            lienzo.paste(celda, (j * w, 0))
        lienzo.save(salida / "_hoja-contacto.png")

    if corte is not None:
        print(f"\n· la continuidad se rompe en el {corte:03d}: {fiables} fiables")
    if args.publicar:
        # Nunca más allá del tramo fiable, aunque se pidan más.
        publicar(salida, min(args.publicar, fiables) or fiables, args.calidad_publicada)

    print(f"\n{len(marcos)} fotogramas en {salida}")
    print("MIRA `_hoja-contacto.png` antes de darlos por buenos: arriba la")
    print("segmentación no tiene de dónde agarrarse y falla sin avisar.")


def publicar(salida, cuantos, calidad):
    """Deja en `web/public/culmo/` los N primeros, recortados a su caja común.

    LA CALIDAD AQUÍ ES MÁS AGRESIVA QUE EN EL ARCHIVO (70 contra 82), por lo
    mismo que en `empacar-360.py`: esto se sirve, aquello se guarda. Y esta capa
    lo tolera mejor que la mayoría — va encima de la fotografía de la que salió,
    desenfocada por detrás y hundida por el velo, así que su detalle fino no se
    mira nunca a solas.

    SOLO LOS PRIMEROS, Y ESO ES UNA DECISIÓN, no una limitación temporal. La
    segmentación es buena mientras el sujeto se separa del fondo —el brote y el
    arranque del culmo— y a partir de ahí la máscara engorda hasta contener una
    columna de bosque entera (la cobertura pasa de 6,7 % a 20,5 % entre el 0 y
    el 24 y ahí se estanca). Publicar los de arriba sería publicar fondo
    recortado disfrazado de sujeto.

    RECORTADOS A LA CAJA COMÚN, no al fotograma entero. El sujeto ocupa 311 px
    de los 1280, o sea que servir el marco completo es servir un 76 % de nada:
    píxeles transparentes que igual hay que descargar y decodificar. La caja se
    calcula sobre TODOS los fotogramas publicados y es una sola, para que el
    navegador pueda dibujarlos todos en el mismo sitio sin llevar la cuenta de
    un desplazamiento por fotograma.

    La caja se imprime al terminar: va en los `data-` del componente, porque
    quien dibuja necesita saber dónde cae este recorte dentro del encuadre.
    """
    import json

    publico = RAIZ / "web/public/culmo"
    publico.mkdir(parents=True, exist_ok=True)
    for viejo in publico.glob("*.webp"):
        viejo.unlink()

    marcos = sorted(salida.glob("culmo-*.webp"))[:cuantos]
    x0 = y0 = 10**6
    x1 = y1 = 0
    for ruta in marcos:
        a = np.array(Image.open(ruta))[:, :, 3]
        ys, xs = np.nonzero(a > 8)
        if not len(xs):
            continue
        x0, x1 = min(x0, int(xs.min())), max(x1, int(xs.max()))
        y0, y1 = min(y0, int(ys.min())), max(y1, int(ys.max()))

    ancho_org, alto_org = Image.open(marcos[0]).size
    peso = 0
    for i, ruta in enumerate(marcos):
        im = Image.open(ruta).crop((x0, y0, x1 + 1, y1 + 1))
        destino = publico / f"culmo-{i:03d}.webp"
        im.save(destino, quality=calidad)
        peso += destino.stat().st_size

    caja = {
        "x": round(x0 / ancho_org, 5),
        "y": round(y0 / alto_org, 5),
        "w": round((x1 + 1 - x0) / ancho_org, 5),
        "h": round((y1 + 1 - y0) / alto_org, 5),
    }
    (publico / "caja.json").write_text(json.dumps(caja, indent=2) + "\n")

    print(f"\n· publicados {len(marcos)} en web/public/culmo/  {peso/1024:.0f} KB")
    print(f"  caja (fracción del encuadre): {json.dumps(caja)}")
    print("  va en los `data-` de VidaGuadual.astro")


if __name__ == "__main__":
    main()
