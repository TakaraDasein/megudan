#!/usr/bin/env python3
"""
Gubia — generador de ilustraciones xilográficas para Megudan.

El isotipo de marca no está dibujado con contornos: son *vaciados*. La plancha
es el fondo oscuro y cada trazo crema es madera levantada con la gubia —ancho
variable, puntas afiladas y el temblor de la mano en el filo—.

Reproducir eso a mano en un editor SVG da paths de miles de puntos (es lo que
pasó con las láminas de corte, que por eso terminaron en WebP). Aquí el dibujo
se describe por su *línea media* y este script le pone el cuerpo: engorda la
centerline con un perfil de ancho que muere en los extremos y le mete un
temblor de baja frecuencia. Salen paths de decenas de puntos, no de miles.

Uso:  pnpm dlx nada — es Python puro.
      python3 herramientas/gubia.py
Escribe los SVG en web/src/components/ilustraciones/.

Para retocar un dibujo se edita su función `dibujo_*` y se vuelve a correr.
No edites los .svg generados a mano: se pisan en la siguiente pasada.
"""

import math
import random
from contextlib import contextmanager

# ── Mecánica de la gubia ──────────────────────────────────────────────────

def _ruido(semilla, n, escala):
    """Temblor de baja frecuencia: interpola entre pocos valores al azar.

    Con ruido blanco el trazo sale peludo; el filo de una gubia se desvía en
    curvas largas, no punto a punto. Seis nodos por trazo es lo que mejor
    imita el pulso de la mano sin que el dibujo se deforme."""
    r = random.Random(semilla)
    nodos = [r.uniform(-1, 1) for _ in range(6)]
    fuera = []
    for i in range(n):
        t = i / max(n - 1, 1) * (len(nodos) - 1)
        j = min(int(t), len(nodos) - 2)
        f = t - j
        f = f * f * (3 - 2 * f)  # suavizado
        fuera.append((nodos[j] * (1 - f) + nodos[j + 1] * f) * escala)
    return fuera


def _muestrear(puntos, n):
    """Recorre la polilínea a paso constante de longitud de arco."""
    largos = [0.0]
    for (x0, y0), (x1, y1) in zip(puntos, puntos[1:]):
        largos.append(largos[-1] + math.hypot(x1 - x0, y1 - y0))
    total = largos[-1]
    fuera = []
    for i in range(n):
        d = total * i / (n - 1)
        j = max(k for k in range(len(largos) - 1) if largos[k] <= d)
        tramo = largos[j + 1] - largos[j] or 1e-9
        f = (d - largos[j]) / tramo
        x0, y0 = puntos[j]
        x1, y1 = puntos[j + 1]
        fuera.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
    return fuera


def gubia(puntos, ancho=6, semilla=0, punta=(0.0, 0.0), temblor=1.0, n=None, dec=1):
    """Un trazo de gubia como path cerrado.

    `puntos`  línea media, en coordenadas del viewBox.
    `ancho`   grosor máximo, en el centro del trazo.
    `punta`   grosor relativo en cada extremo (0 = afilado, 1 = a tope).
              Un culmo cortado a escuadra termina en 1; una talla libre en 0.
    `temblor` cuánto se desvía del trazo ideal.
    """
    if n is None:
        # Un punto cada ~14 unidades del viewBox: por debajo de eso el temblor
        # ya no se ve y solo engorda el SVG, que va inlineado en el HTML.
        largo = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(puntos, puntos[1:]))
        # Nunca por debajo de los puntos que trae la línea media: un arco ya
        # viene muestreado y diezmarlo lo facetaba —el mismo problema que sacó
        # a las láminas de corte del vector—.
        n = max(8, len(puntos), min(30, int(largo / 14) + 4))
    r = random.Random(semilla)
    eje = _muestrear(puntos, n)
    desvio = _ruido(semilla * 7 + 1, n, temblor)
    grosor = _ruido(semilla * 13 + 3, n, 0.18)

    izq, der = [], []
    for i, (x, y) in enumerate(eje):
        # normal a la trayectoria
        a = eje[max(i - 1, 0)]
        b = eje[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        largo = math.hypot(dx, dy) or 1e-9
        nx, ny = -dy / largo, dx / largo

        t = i / (n - 1)
        # el ancho muere hacia las puntas según `punta`
        perfil = math.sin(math.pi * t) ** 0.45
        borde = punta[0] * (1 - t) + punta[1] * t
        w = ancho * (borde + (1 - borde) * perfil) * (1 + grosor[i]) / 2

        cx, cy = x + nx * desvio[i], y + ny * desvio[i]
        izq.append((cx + nx * w, cy + ny * w))
        der.append((cx - nx * w, cy - ny * w))

    # `dec` es cuántos decimales lleva cada coordenada. Uno es lo justo para
    # una lámina de 420 unidades vista a 420 px. En el guadual, que va a 560 y
    # con casi cuatrocientos trazos, medio decimal de más son doce kilobytes
    # de HTML por medio píxel que nadie distingue en un borde temblado.
    contorno = izq + der[::-1]
    d = f"M{contorno[0][0]:.{dec}f} {contorno[0][1]:.{dec}f}"
    for x, y in contorno[1:]:
        d += f"L{x:.{dec}f} {y:.{dec}f}"
    return d + "Z"


def arco(cx, cy, rx, ry, a0, a1, pasos=18):
    """Línea media de un arco de elipse: la boca de un culmo, un nudo."""
    return [
        (
            cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / pasos)),
            cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / pasos)),
        )
        for i in range(pasos + 1)
    ]


class Plancha:
    """Acumula trazos y los escupe como SVG."""

    def __init__(self, ancho, alto, titulo, dec=1, encaje=None):
        self.w, self.h, self.titulo = ancho, alto, titulo
        self.dec = dec
        # `encaje` es el `preserveAspectRatio`. Se emite desde aquí porque no
        # existe propiedad CSS que lo cambie: una lámina que tenga que CUBRIR
        # su caja en vez de caber dentro solo puede decirlo en el atributo.
        self.encaje = encaje
        self.paths = []
        self._n = 0

    def talla(self, puntos, **kw):
        """Un vaciado. Se emite envuelto en un <g> con su origen y su ángulo.

        La envoltura es lo que permite animar el tallado desde la hoja de
        estilos: cada gubia se escala en su propia dirección desde el punto
        donde entra el filo, de modo que el trazo *avanza* en vez de aparecer.
        Los datos van como variables CSS y no como transform ya escrito para
        que la animación —y su ausencia bajo prefers-reduced-motion— se decida
        en el componente y no aquí."""
        self._n += 1
        kw.setdefault("semilla", self._n)
        kw.setdefault("dec", self.dec)
        d = gubia(puntos, **kw)
        (x0, y0), (x1, y1) = puntos[0], puntos[-1]
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        self.paths.append(
            f'<g class="gu" style="--x:{x0:.0f}px;--y:{y0:.0f}px;'
            f'--a:{ang:.0f}deg;--i:{self._n}"><path d="{d}"/></g>'
        )
        return self

    @contextmanager
    def grupo(self, clase, **variables):
        """Envuelve en un `<g>` todo lo que se talle dentro del bloque.

        Es lo que permite mecer una caña entera —culmo, nudos, ramas y hojas—
        como una sola pieza: el `<g class="gu">` de cada trazo ya usa su
        `transform` para el tallado, así que un segundo movimiento sobre el
        mismo elemento pisaría al primero. Anidando, cada uno tiene el suyo.

        Las variables van como CSS y no como `transform` escrito, por el mismo
        motivo que en `talla`: el movimiento —y su ausencia bajo
        `prefers-reduced-motion`— se decide en el componente, no aquí.
        """
        inicio = len(self.paths)
        yield self
        dentro = self.paths[inicio:]
        del self.paths[inicio:]
        estilo = ";".join(f"--{k}:{v}" for k, v in variables.items())
        self.paths.append(f'<g class="{clase}" style="{estilo}">{"".join(dentro)}</g>')

    def masa(self, d):
        """Mancha entintada literal, sin pasar por la gubia.

        Entra en el mismo orden de tallado, pero se revela de golpe: una masa
        no se abre con el filo, se entinta.
        """
        self._n += 1
        self.paths.append(f'<g class="gu masa" style="--i:{self._n}"><path d="{d}"/></g>')
        return self

    def svg(self):
        cuerpo = "".join(self.paths)
        par = f'preserveAspectRatio="{self.encaje}" ' if self.encaje else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'{par}fill="currentColor" role="img" aria-label="{self.titulo}">'
            f"{cuerpo}</svg>"
        )


# ── Los dibujos ───────────────────────────────────────────────────────────
#
# Los tres tienen el mismo viewBox: en el visor del calificador las vistas se
# apilan en la misma celda de la rejilla, y si un dibujo fuera más alto que
# otro el panel saltaría al cambiar de opción.

W, H = 420, 260


def dibujo_construccion():
    """Pórtico completo: basa, columna doble, riostra, cercha y cubierta.

    Es el apunte que ya estaba escrito debajo —«del pedestal a la cubierta»—
    pasado a dibujo. Las basas van como masa entintada y no como trazo: son lo
    único de la escena que no es guadua, y el contraste de técnica lo dice sin
    necesidad de rótulo.

    SE DIBUJA PARA EL TAMAÑO MÁS PEQUEÑO EN QUE SE USA, no para el mayor. Vive
    en dos sitios —el visor del calificador, a 420 px, y la tarjeta de
    servicios, a la mitad— y la primera versión estaba pensada solo para el
    primero: a 190 px las diagonales de la cercha se empastaban en una mancha,
    las basas se leían como dos zapatos sueltos y el vano quedaba como un hueco
    vacío del que colgaba un caballete. Tres decisiones salen de ahí:

    - **Menos barras y más gruesas.** La cercha es pendolón y dos diagonales, y
      ninguna gubia baja de 4 unidades de ancho. Lo que no sobrevive a la mitad
      de tamaño no está.
    - **Columnas dobles con sus chaquetas.** Dos culmos por apoyo es como se
      para de verdad un pórtico en guadua, y de paso da al dibujo el peso que
      le faltaba abajo: antes eran dos palos finos bajo una cubierta ancha.
    - **Riostras de rodilla.** Llenan las esquinas del vano —que era el vacío
      que hacía leer el conjunto como un cobertizo— y son, además, la pieza que
      convierte dos columnas y una viga en un pórtico.
    """
    p = Plancha(W, H, "Pórtico en guadua: basa, columna doble, riostra, cercha y cubierta")
    suelo, cordon, apex = 226, 134, 42

    # ── Cubierta. Un faldón grueso con alero, y las correas como travesaños
    # cortos por debajo. Estuvo un momento como dos faldones paralelos y en los
    # aleros se juntaba con el par de la cercha: tres líneas casi paralelas por
    # esquina, que a tamaño pequeño era un borrón. Los travesaños dicen lo
    # mismo —que ahí hay un techo armado y no una línea— sin acompañar al par.
    p.talla([(26, 102), (210, apex - 4), (394, 102)], ancho=10, punta=(.95, .95), temblor=1.0)
    # Dos por faldón y ninguna en el alero: la del extremo quedaba fuera de la
    # cercha, colgando del vuelo, y a tamaño pequeño se leía como una raya
    # suelta en vez de como una correa.
    for t in (.38, .66):
        for s_ in (-1, 1):
            x = 210 + s_ * (184 * t)
            y = apex + 13 + (106 - apex) * t
            p.talla([(x - 9 * s_, y - 4), (x + 9 * s_, y + 6)], ancho=3.4,
                    punta=(.7, .7), temblor=.3)

    # ── Cercha. Pares, cordón, pendolón y dos diagonales: lo justo para que se
    # lea la triangulación a cualquier tamaño.
    p.talla([(76, cordon), (210, apex + 18)], ancho=6.5, punta=(.9, .4), temblor=.9)
    p.talla([(344, cordon), (210, apex + 18)], ancho=6.5, punta=(.9, .4), temblor=.9)
    p.talla([(76, cordon), (344, cordon)], ancho=7.5, punta=(.9, .9), temblor=1.2)
    # El pendolón arranca bajo el encuentro de los pares: naciendo en el
    # vértice asomaba por encima de la cubierta como una púa.
    p.talla([(210, apex + 34), (210, cordon - 3)], ancho=5, punta=(.4, .85))
    # Las diagonales mueren a media altura del pendolón, no junto al vértice:
    # arriba se juntaban con los pares en un haz de cinco líneas que a tamaño
    # pequeño era una mancha. Abajo forman una V que se lee entera.
    p.talla([(140, cordon - 3), (206, apex + 56)], ancho=4.4, punta=(.4, .55), temblor=.6)
    p.talla([(280, cordon - 3), (214, apex + 56)], ancho=4.4, punta=(.4, .55), temblor=.6)

    for x, s in ((96, 1), (324, -1)):
        # ── Columna doble. Los dos culmos y las dos chaquetas que los amarran.
        for dx in (-8, 8):
            p.talla([(x + dx, cordon + 4), (x + dx, suelo - 10)], ancho=7.5,
                    punta=(.9, .95), temblor=.8)
        for y in (168, 200):
            p.talla([(x - 15, y), (x + 15, y)], ancho=4, punta=(.85, .85), temblor=.4)

        # ── Riostra de rodilla. Cierra la esquina del vano y es la pieza que
        # hace pórtico de lo que si no son dos palos y una viga.
        p.talla([(x + 12 * s, cordon + 34), (x + 54 * s, cordon + 5)],
                ancho=5, punta=(.85, .85), temblor=.5)

        # ── Basa. Un dado bajo y ancho, no un zapato: a tamaño pequeño una
        # masa alta se comía el pie de la columna.
        p.masa(f"M{x-21} {suelo+8}L{x-15} {suelo-8}L{x+15} {suelo-8}L{x+21} {suelo+8}Z")

    p.talla([(46, suelo + 17), (374, suelo + 17)], ancho=3.6, punta=(0, 0), temblor=1.4)
    return p


def dibujo_suministro():
    """Atado de rolliza visto de punta, un culmo tendido y la cota de largo.

    Contesta «material despachado», no «obra». Las bocas de punta son la misma
    elipse con pared y cavidad de las láminas de corte, y el cincho es lo que
    vuelve el montón un atado.

    La cota es la pieza que hace el trabajo: es lo único del dibujo que no
    aparece en el pórtico, y es exactamente lo que separa a quien compra de
    quien construye —el que compra pregunta cuánto mide, no cómo se para—.
    Va sin número: el largo lo pone el pedido, y aquí no se inventan datos.
    """
    p = Plancha(W, H, "Atado de guadua rolliza, un culmo tendido y su cota de largo")

    r, cx0, fila = 24, 210, (34, 79, 124)
    bocas = [
        (cx0 - r * 2, fila[2]), (cx0, fila[2]), (cx0 + r * 2, fila[2]),
        (cx0 - r, fila[1]), (cx0 + r, fila[1]),
        (cx0, fila[0]),
    ]
    for cx, cy in bocas:
        p.talla(arco(cx, cy, r, r, 0, 360, 22), ancho=4.4, punta=(1, 1), temblor=.7)
        p.talla(arco(cx, cy, r * .58, r * .58, 0, 360, 18), ancho=2.1, punta=(1, 1), temblor=.5)

    # El cincho va delante de las bocas: detrás se pierde entre los anillos.
    p.talla([(cx0 - 80, fila[1] + 6), (cx0 - 30, fila[1] - 2),
             (cx0 + 30, fila[1] - 3), (cx0 + 80, fila[1] + 5)],
            ancho=7, punta=(.8, .8), temblor=.7)
    p.masa(f"M{cx0+72} {fila[1]-4}L{cx0+90} {fila[1]+2}"
           f"L{cx0+84} {fila[1]+18}L{cx0+67} {fila[1]+11}Z")

    y, a, x0, x1 = 176, 13, 34, 392
    p.talla([(x0, y - a), (x1, y - a + 2)], ancho=4.6, punta=(.95, .95), temblor=.9)
    p.talla([(x0, y + a), (x1, y + a + 2)], ancho=4.6, punta=(.95, .95), temblor=.9)
    p.talla(arco(x0, y, 6, a, 90, 270, 12), ancho=4, punta=(.9, .9), temblor=.5)
    p.talla(arco(x1 + 1, y + 2, 6, a, 270, 450, 12), ancho=3.2, punta=(.9, .9), temblor=.5)
    for x in (112, 196, 286):  # el anillo del nudo y el resalte que deja el tabique
        p.talla([(x, y - a + 1), (x - 3, y + a + 1)], ancho=3.6, punta=(.9, .9), temblor=.4)
        p.talla([(x + 7, y - a + 3), (x + 5, y + a - 1)], ancho=1.8, punta=(.6, .6), temblor=.4)

    yc = 228
    p.talla([(x0, yc), (x1, yc)], ancho=3, punta=(.8, .8), temblor=.8)
    for x, s in ((x0, 1), (x1, -1)):
        p.talla([(x, yc - 12), (x, yc + 12)], ancho=3, punta=(.9, .9), temblor=.4)
        p.talla([(x + 15 * s, yc - 7), (x, yc), (x + 15 * s, yc + 7)],
                ancho=2.6, punta=(.1, .1), temblor=.4)
    return p


def dibujo_asesoria():
    """Una unión en corte: boca de pescado, perno pasante y mortero.

    «Lo que revisamos» no es una obra ni un material: es un detalle. Por eso
    este es el único de los tres que lleva llamadas —a, b, c—, y por eso las
    tres coinciden con los tres renglones de la lista de al lado. Sin esa
    correspondencia las letras serían decoración.

    Las letras van talladas y no puestas con tipografía: la plancha no cambia
    de técnica a mitad de dibujo, y además el sitio todavía no tiene las
    tipografías del manual (Condor y The Seasons), así que un rótulo real aquí
    envejecería mal cuando lleguen los .woff2.

    La varilla no lleva tuerca arriba: muere anclada en el entrenudo relleno,
    que es como se resuelve de verdad. Abajo sí sale y apoya contra el culmo.
    """
    p = Plancha(W, H, "Unión en guadua: boca de pescado, perno pasante y mortero")

    CX=176                       # eje del culmo que llega
    Y,A,X0,X1=186,28,16,318      # culmo que recibe
    V=29                         # medio ancho del que llega
    TOPE=Y-A                     # cara superior donde asienta

    # ── culmo que recibe ──
    p.talla([(X0,TOPE),(X1,TOPE+2)], ancho=4.6, punta=(.95,.95), temblor=.9)
    p.talla([(X0,Y+A),(X1,Y+A+2)], ancho=4.6, punta=(.95,.95), temblor=.9)
    for x in (68,300):
        p.talla([(x,TOPE+1),(x-3,Y+A+1)], ancho=3.4, punta=(.9,.9), temblor=.4)

    # ── culmo que llega, a plomo ──
    p.talla([(CX-V,22),(CX-V+2,TOPE-2)], ancho=4.6, punta=(.95,.9), temblor=.8)
    p.talla([(CX+V,22),(CX+V-1,TOPE-2)], ancho=4.6, punta=(.95,.9), temblor=.8)
    p.talla(arco(CX,24,V,7.5,180,360,14), ancho=3.4, punta=(.9,.9), temblor=.4)   # boca de arriba
    p.talla([(CX-V+1,88),(CX+V-1,86)], ancho=3.2, punta=(.9,.9), temblor=.4)    # nudo

    # ── a — boca de pescado: la silla que abraza el culmo de abajo ──
    p.talla([(CX-V+1,TOPE-1),(CX-10,TOPE-16),(CX+10,TOPE-16),(CX+V-1,TOPE-1)],
            ancho=4.2, punta=(.85,.85), temblor=.4)

    # ── b — perno pasante: a trazos donde va por dentro, macizo donde sale ──
    # La varilla no lleva tuerca arriba: muere anclada en el entrenudo relleno,
    # que es como se resuelve de verdad. Abajo sí sale y apoya contra el culmo.
    BX=CX+11
    for y0,y1 in ((TOPE-52,TOPE-40),(TOPE-34,TOPE-22),(TOPE-16,TOPE-4),
                  (TOPE+4,TOPE+16),(TOPE+24,Y+8),(Y+16,Y+A-2)):
        p.talla([(BX,y0),(BX,y1)], ancho=2.8, punta=(.9,.9), temblor=.25)
    p.talla([(BX,Y+A+2),(BX,Y+A+14)], ancho=3.2, punta=(.9,.9), temblor=.3)
    p.masa(f"M{BX-12} {Y+A+13}L{BX+12} {Y+A+13}L{BX+12} {Y+A+24}L{BX-12} {Y+A+24}Z")

    # ── c — mortero en el entrenudo: punteado, que es como se rellena ──
    for dx,dy in [(-38,14),(-26,30),(-14,12),(-2,28),(-34,44),(-20,52),(-8,40),(10,18),
                  (18,34),(6,52),(-30,64),(-12,66),(4,62),(20,50),(-24,-30),(-8,-44),
                  (8,-34),(-16,-16),(6,-14)]:
        x,y=BX+dx,TOPE+dy
        p.talla([(x,y),(x+4.5,y+3.5)], ancho=2.4, punta=(.55,.55), temblor=.2)

    # ── llamadas, en columna a la derecha: ninguna cruza el dibujo ──
    def letra(c,x,y,e=11):
        if c=='a':
            p.talla(arco(x,y,e*.6,e*.6,20,340,14), ancho=2.6, punta=(.2,.2), temblor=.25)
            p.talla([(x+e*.6,y-e*.55),(x+e*.6,y+e*.75)], ancho=2.6, punta=(.6,.6), temblor=.25)
        elif c=='b':
            p.talla([(x-e*.58,y-e*1.6),(x-e*.58,y+e*.72)], ancho=2.6, punta=(.6,.6), temblor=.25)
            p.talla(arco(x,y+e*.06,e*.58,e*.6,118,422,14), ancho=2.6, punta=(.2,.2), temblor=.25)
        else:
            p.talla(arco(x,y,e*.6,e*.6,48,312,14), ancho=2.6, punta=(.25,.25), temblor=.25)

    LX=364
    for c,ly,tx,ty in (('a',TOPE-16,CX+V+2,TOPE-10),
                       ('b',Y+A+18,BX+14,Y+A+18),
                       ('c',Y+8,BX+22,TOPE+34)):
        letra(c,LX,ly)
        p.talla([(LX-14,ly),(tx+8,ty)], ancho=1.9, punta=(.15,.1), temblor=.5)
    return p


# ── Los dibujos de obra ───────────────────────────────────────────────────
#
# Uno por proyecto, en la cabecera de su ficha. Comparten viewBox con los del
# calificador —y por tanto peso de trazo y aire— pero no se mezclan con ellos:
# los de arriba contestan «qué necesitas» y estos dicen «qué es esta obra».
#
# Cada uno es el gesto que define su proyecto, no un resumen. Por eso la Casa
# Anolaima no lleva el pórtico completo, que sería el mismo dibujo del
# calificador con otro nombre, sino la cercha sola: la pieza que se arma en el
# suelo y se iza entera, que es lo que cuentan sus fotos.


def dibujo_cercha():
    """Cercha de par y nudillo apoyada en dos pies derechos. — Casa Anolaima.

    Se arma completa en el suelo y sube de una pieza. El dibujo la muestra ya
    posada sobre la placa: los pies van cortados a escuadra —punta a tope— y
    la placa es masa, que es lo único de la escena que no es guadua.
    """
    p = Plancha(W, H, "Cercha de guadua de par y nudillo sobre sus pies derechos")
    apex, cordon, suelo = 44, 150, 226
    izq, der = 62, 358

    p.talla([(izq, cordon), (210, apex)], ancho=8.5, punta=(.9, .4), temblor=1.0)
    p.talla([(der, cordon), (210, apex)], ancho=8.5, punta=(.9, .4), temblor=1.0)
    p.talla([(izq, cordon), (der, cordon)], ancho=7.5, punta=(.9, .9), temblor=1.3)
    p.talla([(136, 100), (284, 100)], ancho=5.2, punta=(.85, .85), temblor=.8)   # nudillo
    p.talla([(210, apex + 12), (210, cordon - 3)], ancho=4.2, punta=(.35, .8))   # pendolón
    p.talla([(136, 104), (206, cordon - 4)], ancho=3.6, punta=(.4, .6), temblor=.6)
    p.talla([(284, 104), (214, cordon - 4)], ancho=3.6, punta=(.4, .6), temblor=.6)

    for x in (98, 322):
        p.talla([(x, cordon + 4), (x, suelo - 10)], ancho=8, punta=(.9, .95), temblor=.8)
        p.talla(arco(x, 190, 9.5, 3.2, 205, 335), ancho=3.2, punta=(.3, .3), temblor=.3)
    p.masa(f"M52 {suelo - 6}L368 {suelo - 6}L368 {suelo + 8}L52 {suelo + 8}Z")
    return p


def dibujo_muro_tierra():
    """Muro de tapia: sobrecimiento de piedra, tongadas y encofrado. — Casa 4 Gatos.

    No hay guadua en el dibujo porque no la hay en el muro. El contraste de
    técnica se mueve: la piedra va como masa —un canto rodado es mancha, no
    filo— y la tierra pisada va tallada, tongada por tongada. El encofrado que
    sube se talla más fino y sin apoyarse en nada: es lo único provisional.
    """
    p = Plancha(W, H, "Muro de tapia pisada: sobrecimiento de piedra, tongadas y encofrado")
    x0, x1 = 104, 316
    coron, base = 76, 208
    suelo = 236

    p.talla([(28, suelo), (392, suelo)], ancho=3.4, punta=(0, 0), temblor=1.4)

    # Sobrecimiento: los cantos van entintados y en hilada corrida, tocando el
    # muro por arriba y el terreno por abajo. Sueltos y menudos se leían como
    # gravilla flotando; es lo contrario de lo que hacen —son la franja que
    # separa la tierra pisada del suelo húmedo, y por eso deben verse macizos.
    for i, (cx, r) in enumerate(((118, 20), (150, 18), (183, 20), (216, 19),
                                 (249, 20), (281, 18), (309, 17))):
        yc = base + 14 + (i % 2) * 2
        p.masa(f"M{cx - r} {yc - 2}L{cx - r * .55} {yc - 14}L{cx + r * .6} {yc - 13}"
               f"L{cx + r} {yc - 1}L{cx + r * .45} {yc + 13}L{cx - r * .6} {yc + 12}Z")

    # El cuerpo de tierra y sus tongadas. Las juntas van de canto a canto: si se
    # quedan cortas el muro se lee como una reja y no como una masa. Por lo
    # mismo no se dibuja el encofrado —dos verticales más por fuera y el dibujo
    # se vuelve un andamio—; que la tapia sube por tongadas ya lo dice el texto.
    p.talla([(x0, base), (x0 + 2, coron)], ancho=7, punta=(.95, .95), temblor=.9)
    p.talla([(x1, base), (x1 - 2, coron)], ancho=7, punta=(.95, .95), temblor=.9)
    for y in (182, 156, 130, 104):
        p.talla([(x0 - 1, y), (x1 + 1, y + 2)], ancho=3.4, punta=(.9, .9), temblor=1.1)

    # viga de coronación
    p.talla([(92, coron), (328, coron + 2)], ancho=8, punta=(.95, .95), temblor=1.0)
    return p


def dibujo_basa():
    """Columna sobre basa, con entrepiso de esterilla. — Casa Charguayacpo.

    La columna no toca el suelo: la basa de concreto la levanta de la humedad,
    y por eso va entintada —es lo único que no es guadua— justo debajo del
    culmo. El entrepiso se dibuja por su canto: la viga y, encima, la esterilla
    a paso corto, que es como se ve desde fuera antes de que haya muros.
    """
    p = Plancha(W, H, "Columna de guadua sobre basa de concreto, con entrepiso de esterilla")
    suelo, piso, alto = 232, 140, 46
    izq, der = 120, 300

    p.talla([(24, suelo + 4), (396, suelo + 4)], ancho=3.4, punta=(0, 0), temblor=1.4)

    for x in (izq, der):
        p.masa(f"M{x - 21} {suelo + 4}L{x - 15} {suelo - 22}L{x + 15} {suelo - 22}"
               f"L{x + 21} {suelo + 4}Z")
        p.talla([(x, suelo - 26), (x, alto + 4)], ancho=8.5, punta=(.95, .95), temblor=.9)
        for y in (196, 96):
            p.talla(arco(x, y, 10, 3.4, 205, 335), ancho=3.2, punta=(.3, .3), temblor=.3)

    p.talla([(92, piso), (328, piso + 2)], ancho=7.5, punta=(.9, .9), temblor=1.1)   # viga
    p.talla([(92, alto), (328, alto + 2)], ancho=7.5, punta=(.9, .9), temblor=1.1)   # carrera
    for x in range(104, 321, 18):                                                    # esterilla
        p.talla([(x, piso - 6), (x, piso - 22)], ancho=2.4, punta=(.7, .7), temblor=.35)
    p.talla([(96, piso - 24), (324, piso - 22)], ancho=3, punta=(.85, .85), temblor=.9)
    return p


def dibujo_arco():
    """Tablero y cubierta en arco, cosidos por montantes. — Puente Sumak.

    Las dos curvas son la misma parábola a distinta altura: la guadua se curva
    sin quebrarse, y eso es lo que deja subir y bajar el puente en un gesto
    continuo. Los estribos van entintados —son lo único fijo al terreno— y el
    agua es un trazo suelto, sin apoyarse en nada.
    """
    p = Plancha(W, H, "Puente de guadua: tablero en arco, cubierta curva y montantes")

    def parabola(f, a, b, n=16):
        return [(a + (b - a) * i / n, f(a + (b - a) * i / n)) for i in range(n + 1)]

    tablero = lambda x: 214 - 62 * (1 - ((x - 210) / 150) ** 2)
    baranda = lambda x: tablero(x) - 24
    cubierta = lambda x: 116 - 58 * (1 - ((x - 210) / 150) ** 2)

    for x in (58, 362):
        p.masa(f"M{x - 34} {228}L{x + 34} {228}L{x + 34} {240}L{x - 34} {240}Z")

    p.talla(parabola(cubierta, 48, 372), ancho=8.5, punta=(.45, .45), temblor=1.0)
    p.talla(parabola(lambda x: cubierta(x) + 13, 66, 354), ancho=3.4, punta=(.5, .5), temblor=.7)
    p.talla(parabola(tablero, 56, 364), ancho=7.5, punta=(.85, .85), temblor=1.0)
    p.talla(parabola(baranda, 76, 344), ancho=3.4, punta=(.5, .5), temblor=.7)

    for x in (94, 152, 210, 268, 326):
        p.talla([(x, tablero(x) - 2), (x, cubierta(x) + 5)], ancho=4, punta=(.85, .85), temblor=.5)

    p.talla([(30, 250), (390, 250)], ancho=3, punta=(0, 0), temblor=1.6)
    return p


def dibujo_capitel():
    """El capitel radial visto en planta. — Restaurante Sumak.

    La columna del centro se abre en abanico hasta formar un anillo, y en ese
    hueco se abre el lucernario. Es a la vez el apoyo del techo y la única
    lámpara del día, así que el dibujo se mira desde abajo: en planta el
    abanico se lee y en alzado no. Los culmos se tallan en orden alrededor del
    anillo, de modo que el tallado gira.
    """
    p = Plancha(W, H, "Capitel radial en planta: los culmos se abren en abanico alrededor del lucernario")
    cx, cy = 210, 130
    r_luz, r_amarre, r_out = 30, 64, 118

    p.talla(arco(cx, cy, r_luz, r_luz, 0, 360, 24), ancho=5, punta=(1, 1), temblor=.7)

    for k in range(16):
        a = math.radians(k * 22.5)
        ca, sa = math.cos(a), math.sin(a)
        p.talla([(cx + r_luz * ca, cy + r_luz * sa), (cx + r_out * ca, cy + r_out * sa)],
                ancho=6, punta=(.9, .35), temblor=.7)

    p.talla(arco(cx, cy, r_amarre, r_amarre, 0, 360, 24), ancho=2.6, punta=(1, 1), temblor=.5)
    p.talla(arco(cx, cy, r_out - 16, r_out - 16, 0, 360, 28), ancho=2.2, punta=(1, 1), temblor=.6)
    return p


# ── Los dibujos de cantidad ───────────────────────────────────────────────
#
# El paso «¿Cuánta necesitas?» no se contesta con un objeto distinto por
# opción: se contesta con EL MISMO objeto a tres escalas. Son bocas de culmo
# vistas de punta —las mismas del atado— y lo único que cambia entre los tres
# dibujos es cuántas hay y cuánto miden. Puestos uno tras otro mientras el
# cursor recorre la lista, la mano ve crecer el pedido; con tres motivos
# distintos vería tres ilustraciones y no una cantidad.
#
# Por eso el radio baja y el conteo sube a la vez: si el atado grande se
# dibujara con bocas del mismo tamaño se saldría del viewBox, y si las tres
# láminas tuvieran el mismo número de bocas a distinto tamaño se leerían como
# un zoom y no como más material.
#
# La cuarta —«necesito ayuda para calcularlo»— rompe la serie a propósito: no
# es una cantidad, es la ausencia de una.

def _boca(p, cx, cy, r, ancho=None):
    """Una boca de culmo: pared y cavidad. El mismo par que el atado."""
    a = ancho if ancho is not None else max(1.8, r * .18)
    p.talla(arco(cx, cy, r, r, 0, 360, max(12, int(r))), ancho=a, punta=(1, 1), temblor=.6)
    # La cavidad solo por encima de cierto radio. En el atado grande las bocas
    # miden 11 unidades de las 420 del viewBox: ahí dentro el anillo interior
    # no se distingue de la pared, pero duplica el número de gubias —y con él
    # el peso del SVG inlineado y el largo del tallado, que va a 22 ms por
    # trazo—. A 30 bocas eso son dos segundos de animación para un detalle que
    # no se ve.
    if r >= 14:
        p.talla(arco(cx, cy, r * .58, r * .58, 0, 360, max(10, int(r * .7))),
                ancho=a * .5, punta=(1, 1), temblor=.45)


def _pila(p, cx, base, r, filas, ancho=None):
    """Una pila piramidal de bocas, `filas` de abajo a arriba.

    Se apilan encajadas —cada hilada monta en el valle de la de abajo—, que es
    como se estiba de verdad y lo que hace que el montón se lea como uno y no
    como bocas sueltas flotando.
    """
    paso = r * 1.74          # altura entre hiladas encajadas
    for i, n in enumerate(filas):
        y = base - i * paso
        x0 = cx - (n - 1) * r
        for k in range(n):
            _boca(p, x0 + k * 2 * r, y, r, ancho)


def dibujo_pocas():
    """Tres culmos de punta, sin cincho. — Menos de 50 piezas.

    Sin cincho a propósito: por debajo de cincuenta piezas no se despacha un
    atado, se despachan culmos. El cincho aparece en la lámina siguiente, y
    esa aparición es la que dice que el pedido cambió de naturaleza.
    """
    p = Plancha(W, H, "Tres culmos de guadua vistos de punta")
    # El radio sale de comparar la lámina con las otras dos, no de que quepa:
    # las tres se miden por cuánta tinta traen, y tres bocas gordas llegaron a
    # tener MÁS superficie dibujada que el atado mediano —el pedido pequeño se
    # veía más grande que el siguiente—. A 30 la escalera queda monótona en
    # tinta y en alto: 8.500 / 10.900 / 12.250 y 60 / 93 / 107.
    for cx in (130, 210, 290):
        _boca(p, cx, 140, 30)
    p.talla([(56, 216), (364, 216)], ancho=3, punta=(0, 0), temblor=1.4)
    return p


def dibujo_media():
    """Un atado cinchado, doce culmos. — Entre 50 y 200.

    El cincho va delante de las bocas y no detrás: entre los anillos se pierde.
    Es la misma decisión que en el atado del primer paso, por el mismo motivo.
    """
    p = Plancha(W, H, "Un atado de guadua cinchado, visto de punta")
    r = 17
    _pila(p, 210, 186, r, (5, 4, 3))
    y = 186 - 1.74 * r
    p.talla([(210 - 5 * r, y + 11), (210 - 2 * r, y), (210 + 2 * r, y), (210 + 5 * r, y + 10)],
            ancho=6, punta=(.8, .8), temblor=.7)
    p.masa(f"M{210+4*r} {y-4}L{210+5*r+10} {y+6}L{210+4*r+4} {y+21}L{210+4*r-12} {y+11}Z")
    p.talla([(56, 216), (364, 216)], ancho=3, punta=(0, 0), temblor=1.4)
    return p


def dibujo_muchas():
    """Una estiba entera, treinta y nueve culmos. — Más de 200.

    La estiba va entintada: es lo único de la escena que no es guadua, igual
    que la placa de la cercha o la basa de la columna. Y es lo que convierte el
    montón en carga —a partir de este volumen el pedido ya no se lleva a mano,
    se estiba y se despacha—.

    Una sola pila y no dos, aunque dos «parezcan más»: la serie crece de verdad
    o no crece. Una pirámide se ACHATA al reducir el radio de la boca, así que
    partir el montón en dos atados chatos daba una lámina más baja que la de
    «entre 50 y 200» —el pedido grande se veía más pequeño que el mediano—.
    Aquí el radio baja a 10 y las hiladas suben a seis: el montón mide 107 de
    alto contra los 93 del atado mediano, y esa diferencia es todo el trabajo
    que hace el dibujo.
    """
    p = Plancha(W, H, "Una estiba de guadua cargada para despacho")
    r, estiba = 10, 214
    _pila(p, 210, estiba - 12, r, (9, 8, 7, 6, 5, 4))

    # El cincho abraza el montón por su hilada más ancha, abajo: arriba, sobre
    # la punta de la pirámide, no ataría nada.
    y = estiba - 12 - 1.74 * r
    p.talla([(210 - 9 * r, y + 12), (210 - 4 * r, y), (210 + 4 * r, y), (210 + 9 * r, y + 11)],
            ancho=5, punta=(.8, .8), temblor=.7)

    p.masa(f"M52 {estiba}L368 {estiba}L368 {estiba+13}L52 {estiba+13}Z")
    for x in (88, 210, 332):
        p.masa(f"M{x-13} {estiba+13}L{x+13} {estiba+13}L{x+13} {estiba+28}L{x-13} {estiba+28}Z")
    # El suelo, como en las otras dos: es lo que las pone en el mismo sitio y
    # deja que la mirada compare los tres montones y no tres encuadres.
    p.talla([(40, estiba + 34), (380, estiba + 34)], ancho=3, punta=(0, 0), temblor=1.5)
    return p


def dibujo_calculo():
    """Croquis acotado, sin números. — Necesito ayuda para calcularlo.

    Rompe la serie porque la opción también la rompe: las otras tres son un
    montón que crece y esta es la que dice que todavía no hay montón. Va sin
    cifras —aquí no se inventan datos, ver contenido/PENDIENTES.md—: lo que se
    dibuja es el trabajo de medir, no el resultado.
    """
    p = Plancha(W, H, "Croquis de cubierta con cotas por resolver")
    # TODO(human)
    return p

# ── Los dibujos de tamaño ─────────────────────────────────────────────────
#
# «¿Qué tamaño?» pregunta metros cuadrados, y un metro cuadrado es área: se
# dibuja en planta o no se dibuja. En alzado los tres tamaños saldrían como
# tres casas de distinta anchura —que es forma, no superficie— y además serían
# tres variantes del pórtico que ya contesta la primera pregunta.
#
# Lo que crece es la retícula: el mismo vano estructural repetido más veces.
# Es la misma mecánica de las tres láminas de cantidad —un solo motivo a tres
# escalas, no tres motivos— y contesta con lo que de verdad decide el precio
# de una obra en guadua, que no son los metros sino cuántos apoyos hay que
# levantar para cubrirlos.
#
# Las columnas van vistas de punta, que en planta es lo que se ve de un culmo:
# la misma boca de las láminas de cantidad, leída desde arriba en vez de desde
# el extremo del atado. Es deliberado que sean el mismo dibujo — quien recorre
# el embudo entero ve la misma pieza contada de dos maneras.

def _reticula(p, cols, filas, paso, r, ancho_viga):
    """Planta de una retícula de columnas con sus vigas.

    `cols` y `filas` son cuántas COLUMNAS hay, no cuántos vanos: una retícula
    de 3×3 columnas encierra 2×2 vanos. Se centra sola en el viewBox, así que
    las tres láminas comparten eje y al pasar de una a otra la planta crece
    desde el centro en vez de saltar de sitio.
    """
    cx, cy = 210, 130
    x = [cx + (i - (cols - 1) / 2) * paso for i in range(cols)]
    y = [cy + (j - (filas - 1) / 2) * paso for j in range(filas)]

    # Las vigas primero: en la plancha van por debajo de las columnas, que es
    # el orden real del montaje leído en planta —la columna remata la viga—.
    for j in y:
        p.talla([(x[0], j), (x[-1], j + 1)], ancho=ancho_viga, punta=(.9, .9), temblor=.8)
    for i in x:
        p.talla([(i, y[0]), (i + 1, y[-1])], ancho=ancho_viga, punta=(.9, .9), temblor=.8)

    for j in y:
        for i in x:
            _boca(p, i, j, r, ancho=max(2.2, r * .26))
    return x, y


def dibujo_area_chica():
    """Un vano: cuatro columnas. — Menos de 60 m².

    Un solo vano cubierto de esquina a esquina. No hay retícula que leer
    todavía; hay una pieza.
    """
    p = Plancha(W, H, "Planta de un vano en guadua: cuatro columnas y sus vigas")
    _reticula(p, 2, 2, 108, 17, 5.5)
    return p


def dibujo_area_media():
    """Cuatro vanos: nueve columnas. — 60 a 150 m².

    Aquí ya hay crujía intermedia, que es lo que cambia de verdad al pasar de
    los 60 m²: el techo deja de resolverse de fachada a fachada.
    """
    p = Plancha(W, H, "Planta de cuatro vanos en guadua: nueve columnas y sus vigas")
    _reticula(p, 3, 3, 76, 12, 4.4)
    return p


def dibujo_area_grande():
    """Nueve vanos y un ala: dieciséis columnas. — Más de 150 m².

    El ala es lo que separa esta lámina de un simple 4×4: por encima de los
    150 m² la planta deja de ser un rectángulo y empieza a tener partes. Va
    con las mismas columnas y el mismo paso —crece la casa, no la escala del
    dibujo—, y se sale del rectángulo por un solo lado para que se lea como
    añadido y no como que la retícula estaba mal centrada.
    """
    p = Plancha(W, H, "Planta de nueve vanos y un ala en guadua: dieciséis columnas")
    paso, r = 56, 9
    x, y = _reticula(p, 4, 4, paso, r, 3.6)

    ala = x[-1] + paso
    p.talla([(x[-1], y[0]), (ala, y[0] + 1)], ancho=3.6, punta=(.9, .9), temblor=.6)
    p.talla([(x[-1], y[1]), (ala, y[1] + 1)], ancho=3.6, punta=(.9, .9), temblor=.6)
    p.talla([(ala, y[0]), (ala + 1, y[1])], ancho=3.6, punta=(.9, .9), temblor=.6)
    for j in (y[0], y[1]):
        _boca(p, ala, j, r, ancho=max(2.2, r * .26))
    return p

# ── Los dibujos de revisión ───────────────────────────────────────────────
#
# El tramo de asesoría no es una escala como los de cantidad y tamaño: sus tres
# opciones no son más y menos de lo mismo, son tres asuntos distintos. Así que
# aquí no hay serie que crezca — hay tres detalles, en el mismo registro que el
# dibujo `union` del primer paso.
#
# Y no se parecen a él a propósito. `union` es el encuentro de dos culmos al
# aire, con sus llamadas; estos tres son el pie que ancla, el tanque que cura y
# la pieza que sale. Si alguno volviera a dibujar una boca de pescado, la
# lámina del primer paso dejaría de significar «asesoría» y pasaría a ser una
# de cuatro uniones.

def dibujo_anclaje():
    """El pie de una columna: basa, platina y perno pasante. — Uniones y anclajes.

    El otro extremo de la estructura. Donde `union` mira dos culmos que se
    encuentran en el aire, este mira el único punto donde la guadua toca algo
    que no es guadua, que es donde se revisa un anclaje: si la platina abraza,
    si el perno apoya contra el entrenudo relleno y si la basa levanta el culmo
    de la humedad.

    Todo lo metálico y lo de concreto va entintado y la guadua tallada: en esta
    lámina el contraste de técnica hace de leyenda —lo que se revisa es
    precisamente el encuentro entre las dos—.
    """
    p = Plancha(W, H, "Anclaje de una columna de guadua: basa de concreto, platina y perno")
    cx, V = 210, 30
    pie, basa, placa, suelo = 178, 214, 228, 240

    # El culmo, que se va por arriba del encuadre: lo que importa está abajo.
    p.talla([(cx - V, 24), (cx - V + 2, pie)], ancho=4.6, punta=(.95, .95), temblor=.8)
    p.talla([(cx + V, 24), (cx + V - 1, pie)], ancho=4.6, punta=(.95, .95), temblor=.8)
    p.talla([(cx - V + 1, 92), (cx + V - 1, 90)], ancho=3.2, punta=(.9, .9), temblor=.4)   # nudo
    p.talla([(cx - V + 1, pie - 6), (cx + V - 1, pie - 8)], ancho=3.2, punta=(.9, .9), temblor=.4)

    # Platina en U: dos alas que abrazan el culmo y una pletina de asiento.
    for lado in (-1, 1):
        x = cx + lado * (V + 9)
        p.masa(f"M{x - 5} {basa - 62}L{x + 5} {basa - 62}L{x + 5} {basa}L{x - 5} {basa}Z")
    p.masa(f"M{cx - V - 16} {basa - 10}L{cx + V + 16} {basa - 10}"
           f"L{cx + V + 16} {basa}L{cx - V - 16} {basa}Z")

    # Perno pasante: macizo donde sale, a trazos donde va por dentro del culmo.
    py = basa - 44
    for x0, x1 in ((cx - V + 4, cx - 10), (cx + 8, cx + V - 4)):
        p.talla([(x0, py), (x1, py)], ancho=2.8, punta=(.9, .9), temblor=.25)
    for lado in (-1, 1):
        x = cx + lado * (V + 14)
        p.masa(f"M{x - 7} {py - 7}L{x + 7} {py - 7}L{x + 7} {py + 7}L{x - 7} {py + 7}Z")

    # Basa de concreto y placa. Lo único que no se revisa: se comprueba que
    # esté, y por eso va como bloque y no como detalle.
    p.masa(f"M{cx - V - 22} {placa}L{cx - V - 14} {basa}L{cx + V + 14} {basa}"
           f"L{cx + V + 22} {placa}Z")
    p.talla([(40, suelo), (380, suelo)], ancho=3, punta=(0, 0), temblor=1.5)
    return p


def dibujo_inmunizado():
    """Culmos en inmersión, cruzando la línea del tanque. — Inmunizado y curado.

    El curado no es una pieza, es un proceso, y lo que se revisa de él no se ve
    en la guadua terminada: se ve en si pasó por aquí. De ahí que el dibujo sea
    el tanque y no un culmo tratado —un culmo tratado y uno sin tratar son el
    mismo dibujo—.

    Los culmos entran inclinados y no en vertical: así cruzan la línea del
    líquido en distinto punto y se lee que están dentro, no delante. El tanque
    va entintado —no es guadua— y la línea del baño va tallada con temblor
    alto, como el suelo de las otras láminas: una superficie, no una pieza.
    """
    p = Plancha(W, H, "Culmos de guadua en inmersión dentro del tanque de inmunizado")
    x0, x1 = 54, 366
    boca_t, fondo, bano = 112, 214, 138

    for x in (x0, x1):                                   # paredes
        p.masa(f"M{x - 9} {boca_t}L{x + 9} {boca_t}L{x + 9} {fondo}L{x - 9} {fondo}Z")
    p.masa(f"M{x0 - 9} {fondo}L{x1 + 9} {fondo}L{x1 + 9} {fondo + 14}L{x0 - 9} {fondo + 14}Z")

    for i in range(4):
        sup, inf = 96 + i * 62, 150 + i * 62
        p.talla([(sup, 40), (inf, fondo - 12)], ancho=4.4, punta=(.95, .9), temblor=.7)
        p.talla([(sup + 26, 42), (inf + 26, fondo - 10)], ancho=4.4, punta=(.95, .9), temblor=.7)
        p.talla(arco(sup + 13, 42, 13, 5, 180, 360, 12), ancho=3, punta=(.9, .9), temblor=.35)

    # La línea del baño va por delante de los culmos: por detrás no cortaría
    # nada y los culmos se leerían apoyados contra el tanque, no metidos en él.
    p.talla([(x0 - 4, bano), (140, bano + 3), (280, bano - 2), (x1 + 4, bano + 2)],
            ancho=3.4, punta=(.6, .6), temblor=1.6)
    for cx, cy, r in ((150, 168, 4), (196, 186, 3), (262, 160, 3.5), (300, 190, 3)):
        p.masa(f"M{cx-r} {cy}a{r} {r} 0 1 0 {2*r} 0a{r} {r} 0 1 0 {-2*r} 0Z")
    return p


def dibujo_reemplazo():
    """Una vigueta fuera de su sitio y el hueco que deja. — Mantenimiento.

    Reemplazar una pieza es lo que se puede hacer con una estructura en guadua
    y no con una vaciada en concreto, y el dibujo lo dice con un hueco: cuatro
    viguetas en su sitio, una quinta izada por encima y el vano vacío donde
    estaba. El ritmo roto es todo el mensaje — sin el hueco esto sería una
    entrepiso cualquiera con un culmo suelto encima.

    Las carreras siguen enteras por detrás del vano: lo que se cambia es la
    pieza, no la estructura, y eso es exactamente lo que hay que ver.
    """
    p = Plancha(W, H, "Una vigueta de guadua izada fuera de su sitio y el vano que deja")
    arriba, abajo = 118, 224
    huecos = (96, 148, 200, 252, 304)
    falta = huecos[2]

    p.talla([(64, arriba), (336, arriba + 2)], ancho=7, punta=(.9, .9), temblor=1.0)
    p.talla([(64, abajo), (336, abajo + 2)], ancho=7, punta=(.9, .9), temblor=1.0)

    for x in huecos:
        if x == falta:
            continue
        p.talla([(x, arriba + 6), (x + 1, abajo - 6)], ancho=6, punta=(.95, .95), temblor=.6)
        p.talla(arco(x, 176, 8, 2.8, 205, 335), ancho=2.8, punta=(.3, .3), temblor=.3)

    # La pieza izada: inclinada y por encima de la carrera, para que se lea que
    # sale y no que espera apoyada.
    p.talla([(falta - 58, 62), (falta + 62, 40)], ancho=6, punta=(.95, .95), temblor=.7)
    p.talla(arco(falta - 60, 62, 5, 9, 90, 270, 12), ancho=2.8, punta=(.9, .9), temblor=.35)
    p.talla(arco(falta + 64, 40, 5, 9, 270, 450, 12), ancho=2.8, punta=(.9, .9), temblor=.35)
    return p

# ── Rótulos tallados ──────────────────────────────────────────────────────
#
# El logotipo de Megudan es letra tallada, no una tipografía: el «Megudan» del
# manual está vaciado con la misma gubia que el isotipo. Así que un titular de
# sección tallado no es un adorno inventado —es la letra de la marca aplicada
# donde hace falta—.
#
# Para poder tallar palabras hace falta una cosa que no teníamos: un alfabeto
# de *línea media*. Cada letra se describe por el recorrido del filo —una o dos
# pasadas— y la gubia le pone el cuerpo, igual que a una cercha. No es una
# fuente y no pretende serlo: solo están las letras que se usan, y se añaden a
# mano las que hagan falta.
#
# **Hoy no hay ningún rótulo tallado en el sitio, y es a propósito.** Se probó
# el titular «Obra construida» de la portada: tallado se ve bien y es la lengua
# del logotipo, pero puesto al lado de Archivo y Fraunces desentona —dos
# escrituras distintas compitiendo en la misma pantalla—. La talla se queda
# donde no hay letra que la contradiga: los dibujos. El alfabeto se conserva
# porque el trabajo ya está hecho y la firma de la marca sí es letra tallada;
# para usarlo:
#
#     p = Plancha(_ancho_de("Obra") + 52, BASE + 26, "Obra")
#     palabra(p, "Obra", 26)
#
# La caja de la letra: la base en 140, la altura de las mayúsculas en 18 y la
# de la x en 58. Sin descendentes por ahora —«Obra construida» no tiene—.

BASE, ALTA, EQUIS = 140, 18, 58


def _o(cx, cy, rx, ry):
    """Un óvalo en dos pasadas que se solapan en las puntas.

    De una sola no se puede: la gubia afila los extremos y el trazo se cerraría
    sobre sí mismo con una muesca a la vista. Dos medias vueltas con 20° de
    solape esconden el empalme donde la letra es más gruesa."""
    return [arco(cx, cy, rx, ry, -100, 100, 16), arco(cx, cy, rx, ry, 80, 280, 16)]


# Cada letra devuelve (trazos, avance). El avance es el ancho de la letra más
# su hombro derecho; el izquierdo va ya metido en las coordenadas.
_LETRAS = {
    " ": (lambda: ([], 46)),
    "O": (lambda: (_o(56, (ALTA + BASE) / 2, 48, (BASE - ALTA) / 2), 122)),
    # El ojo va en una sola pasada que sale del asta y vuelve a ella: los dos
    # empalmes caen sobre el asta, donde la letra ya es maciza, y no se ve la
    # muesca que deja el filo al entrar. Suelto —solo el arco— el ojo quedaba
    # despegado y la b se leía como una ce con palo.
    "b": (lambda: ([[(12, ALTA), (10, BASE)],
                    [(12, 62)] + arco(50, 99, 40, 41, -90, 90, 14) + [(12, 136)]], 98)),
    "d": (lambda: ([[(88, ALTA), (90, BASE)],
                    [(88, 136)] + arco(50, 99, 40, 41, 90, 270, 14) + [(88, 62)]], 98)),
    "r": (lambda: ([[(12, EQUIS), (10, BASE)],
                    arco(46, 88, 34, 30, 180, 285, 10)], 68)),
    "a": (lambda: (_o(46, 99, 36, 41) + [[(84, EQUIS + 4), (82, BASE)]], 100)),
    "c": (lambda: ([arco(48, 99, 38, 41, 52, 308, 18)], 92)),
    "o": (lambda: (_o(48, 99, 38, 41), 100)),
    "n": (lambda: ([[(12, EQUIS), (10, BASE)],
                    arco(48, 90, 36, 32, 180, 360, 12),
                    [(84, 90), (84, BASE)]], 100)),
    "s": (lambda: ([[(80, 68), (54, 57), (26, 64), (24, 82), (52, 96),
                     (78, 108), (78, 130), (48, 141), (20, 132)]], 96)),
    "t": (lambda: ([[(40, 30), (38, 124), (58, 141)],
                    [(12, 62), (70, 59)]], 78)),
    # El cuenco de la u va por abajo: `arco` interpola el ángulo de largo, y
    # con la y creciendo hacia abajo el 90 es el punto bajo. De 180 a 0 pasa
    # por ahí; de 180 a 360 pasaría por arriba y saldría una ene.
    "u": (lambda: ([[(12, EQUIS), (12, 110)],
                    arco(48, 110, 36, 30, 180, 0, 12),
                    [(84, EQUIS), (84, BASE)]], 100)),
    "i": (lambda: ([[(12, EQUIS), (11, BASE)]], 34)),
}

# La i lleva punto, y el punto no se talla: se entinta. Se anota aparte porque
# es lo único del alfabeto que no es un recorrido del filo.
_PUNTOS = {"i": (11, 34, 6.5)}


def palabra(p, texto, x, tracking=0, ancho=15.5, temblor=.7):
    """Talla una palabra sobre la plancha `p`, empezando en `x`.

    Devuelve dónde termina, para poder encadenar o centrar. Cada letra se
    talla con su propia semilla —la que lleva la plancha—, así que dos «a» de
    la misma palabra no salen calcadas: es lo que hace que se lea como talla y
    no como tipografía repetida."""
    for letra in texto:
        if letra not in _LETRAS:
            raise KeyError(f"la gubia no tiene tallada la letra {letra!r}")
        trazos, avance = _LETRAS[letra]()
        for t in trazos:
            p.talla([(px + x, py) for px, py in t],
                    ancho=ancho, punta=(.55, .55), temblor=temblor)
        if letra in _PUNTOS:
            dx, dy, r = _PUNTOS[letra]
            cx, cy = x + dx, dy
            p.masa(f"M{cx-r:.0f} {cy:.0f}a{r:.0f} {r:.0f} 0 1 0 {2*r:.0f} 0"
                   f"a{r:.0f} {r:.0f} 0 1 0 {-2*r:.0f} 0Z")
        x += avance + tracking
    return x - tracking


def _ancho_de(texto, tracking=0):
    total = sum(_LETRAS[l]()[1] + tracking for l in texto)
    return total - tracking


# ── Iconos ────────────────────────────────────────────────────────────────
#
# Un icono no es una ilustración en pequeño: se mira a 22 px, así que lleva
# menos trazos, más gruesos y con menos temblor —a ese tamaño el pulso se lee
# como suciedad, no como talla—. Van en su propio viewBox cuadrado.


def dibujo_equis():
    """La ✕ de cerrar.

    Dos tajos cruzados con las puntas afiladas: es el gesto de la gubia, no la
    equis de una tipografía. Se talla en `currentColor`, de modo que hereda el
    color de donde se ponga y sirve igual sobre el visor de obra que en
    cualquier otro cierre que aparezca después.
    """
    # El ancho es proporcional al viewBox, no absoluto: 5 unidades en una
    # lámina de 420 es un trazo fino y en una de 48 es un garrote. A 3,2 el
    # tajo conserva el perfil de la gubia sin cerrarse sobre sí mismo en el
    # cruce, que es donde se suman los dos.
    p = Plancha(48, 48, "Cerrar")
    p.talla([(11, 11), (37, 37)], ancho=3.2, punta=(0, 0), temblor=.4, semilla=3)
    p.talla([(37, 11), (11, 37)], ancho=3.2, punta=(0, 0), temblor=.4, semilla=11)
    return p


DIBUJOS_ICONO = {
    "equis": dibujo_equis,
}


# ── La vida de la caña ────────────────────────────────────────────────────
#
# Los tres hitos de «Por qué guadua», en la sección de servicios: seis meses,
# cuatro a seis años, décadas. Ilustran un dato que ya estaba escrito, así que
# cada dibujo enseña EXACTAMENTE lo que dice su renglón y nada más —el brote que
# alcanza su altura, el corte que deja la mata en pie, el culmo que dura bajo
# cubierta—. Nada de especies, secciones ni luces: eso está sin confirmar.
#
# Van en su propio viewBox, más pequeño y casi cuadrado, y no en el de 420×260
# de los otros: aquí el sujeto es vertical —una caña que crece— y se mira en una
# columna de un tercio de la mitad de la página, unos 150 px. Con el viewBox
# ancho de los demás el dibujo llegaría a esa columna reducido a un tercio y el
# trazo se rompería. Los anchos de gubia están en unidades del viewBox, así que
# al encoger la lámina hay que encoger el trazo en la misma proporción: por eso
# un culmo aquí va a 6 y no a 8,5.

VW, VH = 200, 190
SUELO = 168


def _culmo(p, x, y0, y1, ancho=6, nudos=(), punta=(.95, .92), temblor=.8):
    """Un culmo a plomo con sus nudos. Los tres dibujos lo repiten.

    El nudo es el resalte del tabique, y se talla un pelo más ancho que el
    culmo: es lo que hace que una caña se lea como caña y no como un palo.
    """
    p.talla([(x, y1), (x, y0)], ancho=ancho, punta=punta, temblor=temblor)
    for y in nudos:
        p.talla([(x - ancho * 1.1, y), (x + ancho * 1.1, y - 1)],
                ancho=ancho * .62, punta=(.85, .85), temblor=.3)


def dibujo_brote():
    """Un renuevo al lado del culmo hecho, y la cota de altura. — 6 MESES.

    El renglón dice «alcanza su altura», así que el dibujo tiene que hablar de
    ALTURA y no de tiempo: dos cañas de la misma mata a distinta edad no lo
    dirían solas —parecerían dos cañas—, y la cota vertical es lo que convierte
    el par en una medida. Va sin número, como la del atado: la altura depende
    del guadual y aquí no se inventan datos.

    El renuevo se distingue por dos cosas y ninguna es el tamaño: muere en punta
    —`punta=(.95, 0)`, el filo levantándose hasta salir— y lleva las hojas
    caulinares abrazándolo, que es como se ve un brote de seis meses en campo.
    """
    p = Plancha(VW, VH, "Un renuevo de guadua junto a un culmo hecho, con su cota de altura")

    # ── El culmo hecho. Llega arriba del todo: es la cota que el brote alcanza.
    _culmo(p, 116, 20, SUELO - 4, ancho=6, nudos=(140, 108, 76, 46))
    # Dos hojas en la punta, cortas: la caña adulta ya solo tiene follaje arriba.
    p.talla([(116, 30), (146, 16)], ancho=2.6, punta=(.5, 0), temblor=.5)
    p.talla([(116, 40), (88, 24)], ancho=2.6, punta=(.5, 0), temblor=.5)

    # ── El renuevo. Más grueso en la base y afilado arriba: sube en punta.
    _culmo(p, 62, 74, SUELO - 4, ancho=6.6, nudos=(146, 118), punta=(.95, 0), temblor=1.0)
    # Las hojas caulinares, envainando el brote. Van abrazadas al tallo y hacia
    # arriba: caídas se leían como maleza a los pies.
    for y, s in ((132, -1), (104, 1), (86, -1)):
        p.talla([(62, y + 6), (62 + 22 * s, y - 10)], ancho=3.4, punta=(.8, 0), temblor=.5)

    # ── El suelo, y el rizoma del que salen los dos. Es lo que dice que son la
    # misma mata y no dos plantas: sin él, la cota compararía cosas distintas.
    p.talla([(14, SUELO), (186, SUELO + 2)], ancho=2.6, punta=(0, 0), temblor=1.4)
    p.talla([(50, SUELO + 12), (88, SUELO + 16), (128, SUELO + 11)],
            ancho=4.2, punta=(.2, .2), temblor=.7)

    # ── La cota, a la derecha y sin número. Cruza de la punta del culmo al
    # suelo, con los remates en aspa de las cotas del atado.
    cx = 176
    p.talla([(cx, 22), (cx, SUELO - 2)], ancho=2.4, punta=(.8, .8), temblor=.6)
    for y, s in ((22, 1), (SUELO - 2, -1)):
        p.talla([(cx - 11, y + 7 * s), (cx, y), (cx + 11, y + 7 * s)],
                ancho=2.2, punta=(.1, .1), temblor=.3)
    return p


def dibujo_corte():
    """La mata en pie con un culmo ya cortado y un renuevo. — 4–6 AÑOS.

    El renglón dice dos cosas —que se corta y que la mata no muere— y el dibujo
    tiene que decir las dos a la vez: si solo se ve el corte, es tala.

    Por eso el que se lleva la gubia es el del medio, y queda como TOCÓN por
    encima de su primer nudo, que es la altura a la que se corta de verdad: el
    tocón lleno de agua pudre la cepa. A los lados quedan dos culmos enteros y
    abajo un renuevo en punta; el corte va a bisel y con su boca, la misma
    elipse con pared de la lámina de cortes.
    """
    p = Plancha(VW, VH, "Un culmo cortado sobre el nudo, la mata en pie y un renuevo")

    # ── Los dos que se quedan. Distinta altura a propósito: un guadual no es
    # una empalizada, y con las tres puntas a la misma cota el dibujo se leía
    # como una valla.
    _culmo(p, 46, 26, SUELO - 4, ancho=5.6, nudos=(138, 106, 74, 48))
    _culmo(p, 156, 40, SUELO - 4, ancho=5.6, nudos=(146, 116, 86, 62))
    for x, y, dx in ((46, 34, -24), (156, 48, 26)):
        p.talla([(x, y), (x + dx, y - 14)], ancho=2.4, punta=(.5, 0), temblor=.5)

    # ── El cortado. El tocón sube hasta poco más del nudo de los 128.
    # Bastante tocón para que se lea como caña cortada y no como brote: por
    # debajo de un tercio de la altura de sus vecinas, la del medio parecía la
    # cría de la mata y el dibujo decía otra cosa.
    corte = 96
    # Punta a tope arriba (`.98`): un culmo cortado termina a escuadra. Con el
    # filo afilado —que es lo que hace la gubia por defecto— el tocón salía en
    # punta y se leía como estaca clavada, justo lo contrario de lo que dice
    # el renglón.
    _culmo(p, 101, corte, SUELO - 4, ancho=6, nudos=(150, 118), punta=(.98, .92))
    # El nudo justo debajo del corte: es el que dice que se cortó DONDE se debe.
    p.talla([(93, 112), (109, 111)], ancho=3.8, punta=(.85, .85), temblor=.3)
    # La boca: pared y cavidad, vistas en escorzo desde arriba. El bisel es la
    # inclinación de la elipse, que se consigue subiendo un extremo del eje.
    # Va PEGADA al tope del tocón —no un par de unidades encima—: separada, la
    # elipse se soltaba del culmo y se leía como un ojo flotando.
    p.talla(arco(101, corte + 2, 6.8, 2.9, 0, 360, 20), ancho=2.6, punta=(1, 1), temblor=.35)
    p.talla(arco(101, corte + 2, 3.4, 1.5, 0, 360, 16), ancho=1.5, punta=(1, 1), temblor=.3)

    # ── El renuevo, en punta y sin nudos marcados: es lo que rebrota solo.
    _culmo(p, 130, 104, SUELO - 4, ancho=4.6, nudos=(152,), punta=(.9, 0), temblor=1.0)
    for y, s in ((142, 1), (124, -1)):
        p.talla([(130, y + 5), (130 + 18 * s, y - 8)], ancho=2.8, punta=(.8, 0), temblor=.5)

    p.talla([(14, SUELO), (186, SUELO + 2)], ancho=2.6, punta=(0, 0), temblor=1.4)
    p.talla([(38, SUELO + 12), (96, SUELO + 16), (150, SUELO + 11)],
            ancho=4.2, punta=(.2, .2), temblor=.7)
    return p


def dibujo_cubierta():
    """Una viga de guadua a cubierto, con la lluvia cayendo fuera. — DÉCADAS.

    «Dura bien inmunizada y bajo cubierta» es una condición, no una propiedad,
    y eso es lo que hay que dibujar: la guadua tapada, y el agua cayendo POR
    FUERA del vuelo. Sin la lluvia, el alero es solo un techo; con ella, el
    alero está haciendo su trabajo y el dibujo dice la condición entera.

    La cubierta va como masa entintada y la basa también: es lo único de la
    escena que no es guadua —la misma regla del pórtico—, y ese contraste de
    técnica dice el material sin rótulo.
    """
    p = Plancha(VW, VH, "Viga de guadua bajo un alero, con la lluvia cayendo por fuera")

    # ── La cubierta y su vuelo. El alero sobresale de la viga por la derecha:
    # ese voladizo es toda la explicación del dibujo.
    p.masa("M18 46L164 74L162 86L16 58Z")
    p.talla([(18, 52), (172, 82)], ancho=3.4, punta=(.9, .1), temblor=.6)

    # ── La viga, con sus nudos, bien por dentro de la sombra del alero.
    viga = 108
    p.talla([(24, viga), (150, viga + 4)], ancho=6.4, punta=(.95, .9), temblor=.8)
    for x in (62, 104, 136):
        p.talla([(x, viga - 8), (x - 2, viga + 8)], ancho=3.6, punta=(.85, .85), temblor=.3)

    # ── El pie y su basa. La guadua no toca el suelo: es la otra mitad de durar.
    _culmo(p, 48, viga + 8, SUELO - 12, ancho=6, nudos=(140,))
    p.masa(f"M32 {SUELO + 4}L38 {SUELO - 12}L58 {SUELO - 12}L64 {SUELO + 4}Z")
    p.talla([(14, SUELO + 10), (186, SUELO + 12)], ancho=2.6, punta=(0, 0), temblor=1.4)

    # ── La lluvia, por fuera del vuelo y en diagonal, cayendo con el mismo
    # ángulo que el faldón. Tres trazos finos: más, y el dibujo pasa a ser una
    # tormenta y le quita el sitio a la viga.
    for x, y in ((176, 96), (186, 122), (170, 138)):
        p.talla([(x, y), (x - 7, y + 22)], ancho=2.2, punta=(.15, 0), temblor=.4)
    return p



# ── El guadual del panel ──────────────────────────────────────────────────
#
# Acompaña al titular del calificador, debajo. No contesta ninguna pregunta —
# las tres láminas que contestan la primera se reparten construir, comprar y
# revisar, y repetir cualquiera aquí le quitaría a esa lámina el trabajo de
# distinguir—. Lo que dibuja es de dónde sale todo: la mata en pie, antes del
# corte. Debajo de un titular que pide que le cuenten una idea, la obra
# terminada sería contestar antes de preguntar.
#
# NO ES UN GRUPO DE CAÑAS: ES UNA ESPESURA. Un guadual visto de frente no
# tiene suelo ni cielo en el encuadre —los culmos entran y salen por los dos
# bordes— y lo que llena el hueco entre ellos son las hojas, no el fondo. La
# primera versión dibujaba seis cañas con un penacho arriba, sobre una línea
# de tierra: eso es un jardín, no un guadual. Tres cosas lo cambian:
#
# 1. **La hoja es una lámina, no un trazo.** Lanceolada quiere decir ancha en
#    el medio y en punta por los dos extremos, que es exactamente una gubia con
#    `punta=(0, 0)` y ancho de sobra —largo entre seis—. Como trazo afilado
#    salían pelos; como lámina, se leen a 30 px.
# 2. **Las hojas van en manojo.** En la guadua brotan cinco o siete de la misma
#    rama, abiertas en abanico y caídas por el propio peso. Una suelta no
#    existe en la naturaleza y tampoco aquí.
# 3. **Los culmos se salen por arriba y por abajo.** Sin línea de suelo: el
#    encuadre está dentro del guadual, no delante de él.
#
# ES EL ÚNICO DIBUJO DEL SITIO QUE SE MUEVE SOLO. Los demás se tallan y se
# quedan quietos; este además respira, porque un guadual quieto es madera y un
# guadual mecido es una planta. El viento no se anima aquí: la plancha emite
# cada caña envuelta en un `<g class="viento">` con su origen de giro, su
# amplitud, su periodo y su desfase, y el componente decide qué hacer con eso
# —incluido no hacer nada bajo `prefers-reduced-motion`—.

GW, GH = 560, 400
# El encuadre es 560×340 y no 420 de ancho como el resto de las láminas: este
# dibujo no se mira dentro de una columna sino atravesándola —entra por el
# borde izquierdo de la página y muere antes del formulario—, y estirar una
# lámina de 420 para cubrir ese ancho la habría hecho crecer de alto en la
# misma proporción, empujando la sección entera. Más ancho de viewBox es más
# cañas, no cañas más gordas.
#
# El encuadre es alto de proporción —340 de alto— y no la banda de
# 420×250 con que empezó: alargar las cañas es lo que las hace guadua. Una
# guadua es cuatro veces más esbelta que un bambú de jardín, y en una banda
# baja los culmos salían rechonchos por mucho que se afinara el trazo.
#
# El giro del viento pivota MUY POR DEBAJO del encuadre, donde estaría la
# cepa. Pivotando en el borde inferior las cañas se abanicaban como cerillas
# clavadas en una fila; una guadua de quince metros se mece con un arco tan
# largo que dentro de este recuadro es casi una traslación.
GPIE = GH + 140


def _hoja(p, x, y, ang, largo, esbeltez=7.6, comba=.24, temblor=.28):
    """Una hoja lanceolada: ancha en el medio, en punta por los dos extremos.


    Es una sola gubia con `punta=(0, 0)`: el perfil de ancho del filo ya da la
    forma de la lámina, sin contorno. Por eso una hoja cuesta un path de doce
    puntos y no de doscientos.

    `comba` es cuánto se arquea hacia abajo. Una hoja de guadua no sale recta:
    cuelga de su propio peso, y esa caída es lo que separa un guadual de un
    manojo de cuchillos.
    """
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    f = largo * comba
    p.talla([
        (x, y),
        (x + dx * largo * .45 + nx * f * .8, y + dy * largo * .45 + ny * f * .8),
        (x + dx * largo * .8 + nx * f, y + dy * largo * .8 + ny * f),
        (x + dx * largo + nx * f * .7, y + dy * largo + ny * f * .7 + largo * .1),
    ], ancho=largo / esbeltez, punta=(0, 0), temblor=temblor, n=9)


def _manojo(p, x, y, giro, largo, n=6, abre=64, lado=1, amp="2.4deg",
            dur="3.4s", ret="0s"):
    """Un manojo de hojas con su ramilla, en su propio grupo de viento.

    Va anidado dentro del grupo de la caña: la hoja se mueve lo que se mueve el
    culmo MÁS lo suyo, que es como se comporta de verdad —la hoja bate mucho
    más rápido que el tallo que la sostiene—. Anidar transformaciones es gratis
    y sumar dos animaciones sobre el mismo elemento no se puede.

    LAS HOJAS VAN CASI PARALELAS Y REPARTIDAS POR TODA LA RAMILLA, no abiertas
    en abanico desde la punta. Con el abanico corto —que es como estaba— las
    seis láminas se cruzaban sobre el mismo punto y el manojo se leía como una
    mano: una mancha con dedos. En la guadua la ramilla es larga, las hojas
    salen escalonadas a lo largo de ella y caen casi en la misma dirección, y
    entre lámina y lámina se ve el fondo. Ese hueco es lo que hace que se
    cuenten las hojas en vez de verse un borrón.
    """
    with p.grupo("viento", ox=f"{x:.0f}px", oy=f"{y:.0f}px", amp=amp, dur=dur, ret=ret):
        ra = math.radians(giro)
        rl = largo * 1.5
        p.talla([(x, y),
                 (x + math.cos(ra) * rl * .55, y + math.sin(ra) * rl * .55 + largo * .06),
                 (x + math.cos(ra) * rl, y + math.sin(ra) * rl + largo * .14)],
                ancho=1.5, punta=(.7, .1), temblor=.3)
        for k in range(n):
            t = .12 + .88 * (k / max(n - 1, 1))
            hx = x + math.cos(ra) * rl * t
            hy = y + math.sin(ra) * rl * t + largo * .14 * t * t
            # LAS HOJAS ALTERNAN LADO DE LA RAMILLA, una arriba y otra abajo,
            # como brotan de verdad. Con todas hacia el mismo lado —que es como
            # estaba— las láminas de la base se montaban unas sobre otras y el
            # manojo remataba en una cuña maciza: un ala, no un manojo. Alternar
            # las separa sin tener que abrir más el abanico, que es lo que
            # arruinaría la caída.
            costado = 1 if k % 2 else -1
            ang = giro + costado * abre * .5 * (1 - .35 * t)
            # La lámina se acorta hacia la punta de la ramilla: la silueta del
            # manojo es más ancha por donde nace.
            _hoja(p, hx, hy, ang, largo * (.72 + .38 * (1 - t)),
                  comba=.26 * (1 if costado > 0 else -1) * lado)


def _cana(p, x, cima, ancho, nudos_cada=30, manojos=(), amp="1deg",
          dur="6s", ret="0s", pie=GPIE, base=None, cogollo=None):
    """Una caña entera: culmo, nudos, ramillas y hojas, meciéndose desde la cepa.

    EL CULMO SUBE A PLOMO. Tuvo un `ladeo` —cuánto se apartaba la cima del
    pie— para que el guadual no saliera como una verja, y el remedio era peor:
    catorce cañas cada una con su inclinación se cruzaban entre ellas y el
    conjunto se leía como cañaveral tumbado por el viento, no como guadual. La
    guadua crece a plomo y es lo primero que se ve de una: la variedad tiene
    que venir del grosor, de la altura a la que remata y de dónde cuelga el
    follaje, no de torcerlas.

    LA CAÑA QUE REMATA DENTRO DEL ENCUADRE SE AFILA Y LA QUE SE SALE, NO. Una
    guadua no termina en un canto romo: el culmo adelgaza hasta el cogollo. Si
    `cima` cae dentro del recuadro el trazo muere casi en punta —`0.12`— y se
    le pone su penacho; si se sale por arriba, termina a tope, porque ahí lo
    que corta es el borde del dibujo y no la planta. Mezclar las dos cosas es
    lo que da la altura desigual de un guadual de verdad, donde conviven cañas
    hechas y cañas del año.

    Los nudos son ceja y no anillo completo: a este tamaño el anillo con su
    resalte —el del atado— se empasta contra un culmo de 5 de ancho. Una raya
    corta que asoma por los dos lados dice nudo igual y sobrevive al encogido.
    """
    base = GH + 20 if base is None else base
    with p.grupo("viento", ox=f"{x:.0f}px", oy=f"{pie:.0f}px",
                 amp=amp, dur=dur, ret=ret):
        alto = base - cima

        def sobre(t):
            """Punto del culmo a la altura relativa `t`. Queda como función —y
            no como cuenta suelta— porque los nudos, las ramas y el cogollo se
            colocan por ella: cualquier cosa que le pase al culmo tiene que
            pasarles a ellos en el mismo sitio."""
            return (x, base - alto * t)

        remata = cima > 12   # ¿la cima cae dentro del encuadre?
        p.talla([sobre(0), sobre(.5), sobre(1)],
                ancho=ancho, punta=(.95, .12 if remata else .5), temblor=.85)

        n = max(2, int(alto / nudos_cada))
        for i in range(1, n):
            t = i / n
            nx, ny = sobre(t)
            w = ancho * (1 - .38 * t)  # el culmo adelgaza; el nudo, con él
            p.talla([(nx - w * 1.05, ny + 1.6), (nx + w * 1.05, ny)],
                    ancho=max(1.4, w * .5), punta=(.85, .85), temblor=.2)
            # La cicatriz de la vaina, justo encima del nudo y más fina. Solo
            # en los culmos de delante: en los del fondo dobla el número de
            # trazos para dos píxeles que nadie mira.
            if ancho >= 5:
                p.talla([(nx - w * .8, ny - 6), (nx + w * .8, ny - 6.6)],
                        ancho=1.2, punta=(.7, .7), temblor=.2)

        # El cogollo: el penacho que remata la caña joven. Va aparte de los
        # manojos porque no cuelga de un lado del culmo sino de su punta, y
        # porque solo lo llevan las que rematan dentro del encuadre.
        if cogollo:
            cx_, cy_ = sobre(1)
            _manojo(p, cx_, cy_ + 2, cogollo[0], cogollo[1], n=cogollo[2],
                    abre=cogollo[3], lado=cogollo[4],
                    amp=cogollo[5], dur=cogollo[6], ret=cogollo[7])

        for m in manojos:
            mx, my = sobre(m[0])
            _manojo(p, mx, my, m[1], m[2], n=m[3], abre=m[4], lado=m[5],
                    amp=m[6], dur=m[7], ret=m[8])


def dibujo_guadual():
    """Un guadual visto por dentro, mecido por el viento.

    Tres planos de profundidad. Al fondo, culmos delgados y pálidos sin una
    sola hoja: son la espesura, y a esa distancia el follaje es mancha, no
    dibujo. En el medio, las cañas con sus manojos, que es donde se lee la
    hoja. Delante, dos culmos gruesos con sus nudos y su cicatriz de vaina,
    tan cerca que se salen por arriba y por abajo del encuadre.

    Ninguna caña remata dentro del recuadro y no hay línea de suelo: el que
    mira está DENTRO del guadual. Es la diferencia entre un guadual y unas
    matas de bambú en un jardín, y es lo que hace que un dibujo de catorce
    cañas se lea como un bosque.
    """
    # `xMinYMax slice`: el guadual CUBRE el hueco que le den en vez de caber
    # dentro de él. Encajado —lo que hace un SVG por defecto— dejaba franjas
    # vacías arriba o al costado en cuanto la columna no tenía exactamente su
    # proporción, y una franja vacía en un dibujo que va a sangre se ve como
    # un fallo. Al recortar, lo que se pierde es guadual de sobra por un borde,
    # que es justo lo que un guadual tiene.
    #
    # El ancla es abajo a la izquierda: al pie porque las cañas nacen del borde
    # inferior, y a la izquierda porque ese borde llega al de la página. Lo que
    # se recorta, se recorta por arriba y por la derecha, que son los dos lados
    # donde ya hay un fundido de máscara.
    # ESTA LÁMINA NO SE TALLA GUBIA A GUBIA. Las demás se abren trazo a trazo
    # —es la firma de la casa— y aquí se probó de cinco maneras: por planos, de
    # izquierda a derecha, por manchas, mata a mata y creciendo de abajo
    # arriba. Todas tenían el mismo problema de fondo: ochocientos trazos
    # escalonados son ochocientos sucesos, y por bien repartidos que estén el
    # ojo sigue el reparto en vez de mirar el bosque. Un guadual no es una
    # pieza que se construye a la vista; es un sitio que ya estaba.
    #
    # Así que el escalonado se quitó del generador —no se dejó apagado— y el
    # dibujo entero se revela con UN gesto desde el componente. Por eso aquí no
    # hay nada que decir sobre el orden de los trazos: el `--i` que llevan sigue
    # sirviendo a las otras once láminas y aquí no lo mira nadie.
    p = Plancha(GW, GH, "Un guadual de guadua visto por dentro, mecido por el viento",
                dec=0, encaje="xMinYMax slice")

    # ── Fondo. Culmos delgados, sin hojas. Nudos muy espaciados: a 2,6 de
    # ancho y al 40% de opacidad, marcarlos cada 30 unidades sumaba cincuenta
    # trazos que no se ven y que sí se pagan —el SVG va inlineado en el HTML de
    # la portada—.
    #
    # Los huecos entre ellas son desiguales a propósito —dos casi pegadas,
    # luego un claro—, que es como crece un guadual, por matas. A paso
    # constante el fondo se leía como una empalizada. Y hacia la derecha van
    # más juntas: esa mitad la tapa menos el titular, así que aguanta —y pide—
    # más espesura.
    #
    # Cinco rematan dentro, a alturas distintas: son las cañas del año, y sin
    # ellas las dieciocho terminaban a la misma altura y la fila de arriba
    # salía cortada a nivel, como un seto.
    for x, cima, an, dur, ret in (
        (14, -40, 2.6, "7.4s", "-2.1s"), (30, 62, 2.0, "8.1s", "-5.4s"),
        (68, -40, 2.8, "6.8s", "-1.2s"), (104, -40, 2.3, "7.9s", "-3.8s"),
        (118, 112, 2.1, "8.6s", "-6.2s"), (166, -40, 2.7, "7.1s", "-4.6s"),
        (208, -40, 2.4, "8.4s", "-0.7s"), (252, 74, 2.2, "6.9s", "-2.9s"),
        (296, -40, 2.8, "7.6s", "-5.1s"), (312, -40, 2.1, "8.2s", "-3.4s"),
        (350, -40, 2.5, "7.3s", "-1.8s"), (372, 128, 2.3, "8.0s", "-4.2s"),
        (404, -40, 2.7, "6.7s", "-2.5s"), (424, -40, 2.2, "7.8s", "-5.7s"),
        (462, 40, 2.4, "8.3s", "-0.9s"), (486, -40, 2.9, "7.0s", "-3.0s"),
        (516, -40, 2.3, "8.5s", "-1.4s"), (546, -40, 2.6, "7.2s", "-4.9s"),
    ):
        with p.grupo("lejos"):
            _cana(p, x, cima, an, nudos_cada=64, amp="2.4deg", dur=dur, ret=ret)

    # ── Follaje del fondo: manojos sueltos, sin caña a la vista. Son los que
    # cierran la espesura —a esa distancia no se ve de qué culmo cuelgan— y por
    # eso pueden ponerse justo donde queda hueco. Van en la capa pálida y se
    # mecen desde su propio punto de nacimiento, no desde una cepa.
    for x, y, giro, largo, n, abre, lado, dur, ret in (
        (30, 112, -24, 30, 5, 52, 1, "3.9s", "-1.3s"),
        (88, 60, -156, 28, 4, 48, -1, "4.4s", "-3.6s"),
        (126, 202, -18, 32, 5, 54, 1, "3.5s", "-0.8s"),
        (182, 98, -162, 30, 5, 50, -1, "4.1s", "-2.7s"),
        (214, 250, -26, 27, 4, 46, 1, "4.7s", "-5.2s"),
        (262, 148, -150, 33, 5, 56, -1, "3.7s", "-1.9s"),
        (330, 86, -168, 29, 4, 50, -1, "4.3s", "-4.1s"),
        (52, 304, -156, 26, 4, 46, -1, "4.9s", "-2.4s"),
        (168, 344, -22, 28, 4, 48, 1, "4.2s", "-0.3s"),
        (286, 316, -160, 30, 5, 52, -1, "3.8s", "-3.9s"),
        (352, 232, -28, 27, 4, 48, 1, "4.6s", "-1.6s"),
        (10, 206, -152, 25, 4, 46, -1, "4.4s", "-5.5s"),
        (232, 46, -18, 26, 4, 46, 1, "4.0s", "-2.2s"),
        (74, 372, -164, 27, 4, 48, -1, "4.5s", "-4.8s"),
        (396, 136, -156, 31, 5, 54, -1, "3.6s", "-3.1s"),
        (438, 72, -20, 28, 4, 48, 1, "4.8s", "-0.6s"),
        (466, 272, -162, 29, 5, 50, -1, "4.0s", "-2.0s"),
        (506, 186, -26, 30, 5, 52, 1, "3.4s", "-4.5s"),
        (548, 338, -158, 26, 4, 46, -1, "4.7s", "-1.1s"),
        (404, 352, -24, 27, 4, 48, 1, "4.1s", "-5.8s"),
        (492, 108, -154, 28, 4, 48, -1, "3.9s", "-2.9s"),
        (534, 218, -22, 29, 5, 50, 1, "4.3s", "-0.2s"),
        (368, 292, -160, 26, 4, 46, -1, "4.6s", "-3.4s"),
        (446, 168, -24, 27, 4, 48, 1, "4.2s", "-5.3s"),
    ):
        with p.grupo("lejos"):
            _manojo(p, x, y, giro, largo, n=n, abre=abre, lado=lado,
                    amp="2.8deg", dur=dur, ret=ret)

    # ── Plano medio. Aquí empiezan los manojos, siempre por encima de la mitad:
    # en la guadua las ramas de abajo se caen solas y el culmo queda limpio, que
    # es justo lo que la hace servir para construir.
    _cana(p, 58, -30, 4.6, manojos=[
        (.90, -30, 40, 6, 60, 1, "2.4deg", "3.2s", "-1.1s"),
        (.72, -152, 34, 5, 54, -1, "2.0deg", "3.9s", "-2.4s"),
        (.52, -26, 30, 4, 50, 1, "1.9deg", "4.3s", "-0.5s"),
        (.30, -158, 26, 4, 48, -1, "1.7deg", "4.8s", "-3.2s"),
    ], amp="1.5deg", dur="6.2s", ret="-0.9s")

    _cana(p, 144, -40, 5.0, manojos=[
        (.93, -158, 42, 6, 62, -1, "2.6deg", "3.0s", "-2.2s"),
        (.76, -22, 36, 5, 56, 1, "2.1deg", "3.6s", "-0.4s"),
        (.56, -164, 32, 5, 52, -1, "1.9deg", "4.1s", "-3.7s"),
        (.34, -18, 27, 4, 48, 1, "1.7deg", "4.6s", "-1.4s"),
        (.14, -160, 24, 4, 44, -1, "1.6deg", "5.1s", "-4.3s"),
    ], amp="1.7deg", dur="5.6s", ret="-3.3s")

    _cana(p, 238, -34, 4.4, manojos=[
        (.88, -28, 38, 6, 60, 1, "2.5deg", "3.4s", "-1.8s"),
        (.68, -156, 33, 5, 54, -1, "2.2deg", "4.0s", "-4.4s"),
        (.44, -24, 28, 4, 50, 1, "1.8deg", "4.5s", "-2.1s"),
        (.20, -160, 25, 4, 46, -1, "1.6deg", "5.0s", "-0.7s"),
    ], amp="1.6deg", dur="6.6s", ret="-4.7s")

    _cana(p, 336, -40, 5.2, manojos=[
        (.92, -148, 40, 6, 62, -1, "2.5deg", "3.1s", "-0.6s"),
        (.74, -32, 34, 5, 56, 1, "2.0deg", "3.8s", "-2.9s"),
        (.54, -152, 29, 4, 50, -1, "1.8deg", "4.4s", "-5.0s"),
        (.28, -28, 25, 4, 46, 1, "1.6deg", "4.9s", "-1.7s"),
    ], amp="1.5deg", dur="6.0s", ret="-1.9s")

    _cana(p, 428, -30, 4.7, manojos=[
        (.89, -26, 39, 6, 60, 1, "2.4deg", "3.3s", "-3.8s"),
        (.70, -154, 34, 5, 54, -1, "2.1deg", "3.9s", "-1.2s"),
        (.48, -22, 29, 4, 50, 1, "1.8deg", "4.4s", "-4.9s"),
        (.24, -158, 25, 4, 46, -1, "1.6deg", "5.0s", "-2.6s"),
    ], amp="1.6deg", dur="6.4s", ret="-5.2s")

    _cana(p, 516, -36, 4.9, manojos=[
        (.91, -150, 40, 6, 62, -1, "2.5deg", "3.2s", "-2.0s"),
        (.71, -30, 34, 5, 56, 1, "2.0deg", "3.7s", "-4.6s"),
        (.50, -156, 29, 4, 50, -1, "1.8deg", "4.3s", "-0.4s"),
        (.26, -26, 25, 4, 46, 1, "1.6deg", "4.8s", "-2.8s"),
    ], amp="1.6deg", dur="5.9s", ret="-3.5s")

    # Una más en la mitad derecha, que es la que aguanta espesura: ahí el
    # titular no tapa nada y el dibujo llega hasta el formulario.
    _cana(p, 470, -34, 4.5, manojos=[
        (.87, -30, 37, 6, 58, 1, "2.4deg", "3.5s", "-1.0s"),
        (.66, -156, 32, 5, 54, -1, "2.0deg", "4.0s", "-3.4s"),
        (.42, -24, 28, 4, 50, 1, "1.8deg", "4.6s", "-5.6s"),
    ], amp="1.6deg", dur="6.5s", ret="-2.3s")

    # ── Las cañas jóvenes: rematan a media altura, con su cogollo y RECTAS.
    # Son la variedad de altura del plano medio. Ninguna se arquea: a esa
    # altura la caña se sostiene sola —ver la nota de `_cana`—, y curvarlas era
    # el error que hacía que el guadual pareciera un bambú de maceta.
    _cana(p, 288, 92, 4.0,
          cogollo=(-76, 30, 5, 58, 1, "2.8deg", "3.3s", "-1.5s"), manojos=[
        (.76, -28, 32, 5, 56, 1, "2.5deg", "3.4s", "-1.8s"),
        (.48, -156, 28, 4, 52, -1, "2.2deg", "4.0s", "-4.4s"),
        (.22, -24, 25, 4, 48, 1, "1.8deg", "4.5s", "-2.1s"),
    ], amp="1.9deg", dur="6.0s", ret="-4.7s")

    _cana(p, 190, 176, 3.4, nudos_cada=26,
          cogollo=(-100, 26, 4, 54, -1, "3.0deg", "3.6s", "-2.8s"), manojos=[
        (.62, -160, 26, 4, 50, -1, "2.4deg", "4.2s", "-0.9s"),
        (.32, -20, 23, 4, 46, 1, "2.0deg", "4.7s", "-3.5s"),
    ], amp="2.1deg", dur="5.8s", ret="-2.6s")

    _cana(p, 498, 56, 3.8, nudos_cada=28,
          cogollo=(-16, 29, 5, 56, 1, "2.9deg", "3.5s", "-5.1s"), manojos=[
        (.70, -26, 30, 5, 54, 1, "2.4deg", "3.9s", "-2.3s"),
        (.42, -158, 26, 4, 50, -1, "2.0deg", "4.5s", "-4.0s"),
        (.18, -22, 23, 4, 46, 1, "1.8deg", "5.0s", "-1.0s"),
    ], amp="1.9deg", dur="6.3s", ret="-0.5s")

    _cana(p, 386, 132, 3.6, nudos_cada=26,
          cogollo=(-84, 27, 4, 54, 1, "3.0deg", "3.4s", "-3.9s"), manojos=[
        (.66, -24, 28, 4, 52, 1, "2.4deg", "4.1s", "-1.7s"),
        (.36, -158, 25, 4, 48, -1, "2.0deg", "4.6s", "-4.6s"),
    ], amp="2.0deg", dur="6.1s", ret="-1.2s")

    # ── Dos cañas que rematan muy arriba, casi en el borde, con su cogollo.
    # Entre las que se salen del encuadre y las del año que se quedan a media
    # altura, estas dos son el escalón de en medio: sin ellas el guadual solo
    # tenía cañas enteras y cañas pequeñas.
    _cana(p, 218, 26, 4.2,
          cogollo=(-172, 32, 5, 60, -1, "2.6deg", "3.3s", "-1.5s"), manojos=[
        (.84, -158, 34, 5, 56, -1, "2.3deg", "3.7s", "-4.1s"),
        (.60, -26, 30, 4, 52, 1, "2.0deg", "4.2s", "-2.0s"),
        (.34, -160, 26, 4, 48, -1, "1.8deg", "4.7s", "-5.5s"),
    ], amp="1.8deg", dur="6.4s", ret="-3.0s")

    _cana(p, 404, 18, 4.4,
          cogollo=(-8, 34, 5, 62, 1, "2.6deg", "3.1s", "-4.4s"), manojos=[
        (.86, -22, 35, 5, 58, 1, "2.3deg", "3.6s", "-1.3s"),
        (.62, -156, 30, 4, 52, -1, "2.0deg", "4.1s", "-3.8s"),
        (.36, -20, 26, 4, 48, 1, "1.8deg", "4.6s", "-0.6s"),
    ], amp="1.8deg", dur="6.2s", ret="-5.1s")

    # ── Primer plano. Tres culmos gruesos, entrando y saliendo del encuadre por
    # los dos bordes, que apenas se mueven: son el ancla. Sin ellos las cañas
    # del fondo se mecen sobre nada y el dibujo entero parece temblar.
    _cana(p, 100, -50, 7.4, nudos_cada=44, manojos=[
        (.95, -170, 34, 5, 64, -1, "1.8deg", "3.8s", "-2.6s"),
        (.68, -166, 28, 4, 56, -1, "1.6deg", "4.3s", "-5.4s"),
    ], amp="0.8deg", dur="7.8s", ret="-1.5s")

    _cana(p, 272, -50, 6.8, nudos_cada=44, manojos=[
        (.94, -12, 36, 5, 66, 1, "1.9deg", "3.5s", "-3.1s"),
        (.70, -16, 29, 4, 58, 1, "1.7deg", "4.1s", "-0.8s"),
    ], amp="0.9deg", dur="7.2s", ret="-5.9s")

    _cana(p, 462, -50, 7.0, nudos_cada=44, manojos=[
        (.96, -168, 35, 5, 64, -1, "1.8deg", "3.6s", "-4.2s"),
        (.72, -14, 29, 4, 58, 1, "1.6deg", "4.2s", "-2.3s"),
    ], amp="0.85deg", dur="7.5s", ret="-3.7s")

    return p


DIBUJOS = {
    "portico": dibujo_construccion,
    "atado": dibujo_suministro,
    "union": dibujo_asesoria,
    # El paso de cantidad. Van en la misma carpeta y con el mismo viewBox que
    # los tres de arriba porque comparten celda con ellos en el visor.
    "pocas": dibujo_pocas,
    "media": dibujo_media,
    "muchas": dibujo_muchas,
    "calculo": dibujo_calculo,
    # El paso de tamaño, en el ramal de obra.
    "area-chica": dibujo_area_chica,
    "area-media": dibujo_area_media,
    "area-grande": dibujo_area_grande,
    # El paso de revisión, en el ramal de asesoría.
    "anclaje": dibujo_anclaje,
    "inmunizado": dibujo_inmunizado,
    "reemplazo": dibujo_reemplazo,
}

# Los de obra van en su propia carpeta: no se apilan en la misma celda que los
# del calificador y no hay que cuidar que midan todos lo mismo, pero comparten
# viewBox para que el trazo pese igual en las dos pantallas.
DIBUJOS_OBRA = {
    "cercha": dibujo_cercha,
    "muro-tierra": dibujo_muro_tierra,
    "basa": dibujo_basa,
    "arco": dibujo_arco,
    "capitel": dibujo_capitel,
}

# El guadual del panel del calificador. Carpeta aparte y viewBox propio —ver su
# nota—: es lo único que no se apila con nada, y lo único que se mueve solo.
DIBUJOS_PANEL = {
    "guadual": dibujo_guadual,
}

# ── El cierre: tres planos del guadual ────────────────────────────────────
#
# Acompañan a los tres mensajes del cierre de la portada, donde la secuencia
# desciende del dosel al brote. Cada uno es el PLANO en el que está la cámara
# en ese momento, no un resumen de la frase: arriba la bóveda, a media altura
# el culmo, y abajo lo que no se ve desde ninguna cámara —el rizoma—.
#
# Se miran sobre fotografía en movimiento y a unos 150 px, así que llevan menos
# piezas y más gruesas que los de la sección de servicios: sobre un fondo
# quieto un trazo de 3 unidades se lee, sobre un guadual que se mueve no.
# Ninguno baja de 4.


def dibujo_dosel():
    """Cuatro culmos que se arquean y cierran en bóveda. — EL DOSEL.

    Es el primer fotograma de la secuencia hecho dibujo: la cámara está mirando
    hacia arriba y lo que se ve es el cruce de las copas. Sin suelo y sin
    horizonte a propósito —ahí arriba no hay ninguno de los dos—, que es lo que
    lo distingue de los otros dos planos.

    Los culmos entran por abajo y salen por los lados: el encuadre corta, no
    contiene. Un dibujo con las cuatro cañas enteras dentro del cuadro se leía
    como un ramo.
    """
    p = Plancha(VW, VH, "Copas de guadua cruzándose en bóveda, vistas desde abajo")

    # Cuatro culmos que suben arqueándose y SE CRUZAN, cada uno saliendo por su
    # sitio del borde de arriba. La primera versión los hacía converger en un
    # punto y el dibujo salía un haz atado, que es justo lo contrario de una
    # bóveda: lo que cierra una bóveda es que las piezas se crucen y sigan.
    # Por eso los extremos están FUERA del cuadro (y negativa).
    trazos = [
        ([(30, VH), (40, 118), (78, 48), (146, -14)], 7.2),
        ([(80, VH), (84, 116), (100, 54), (128, -12)], 6.2),
        ([(124, VH), (120, 114), (104, 52), (74, -12)], 6.2),
        ([(172, VH), (162, 120), (124, 50), (54, -14)], 7.2),
    ]
    for i, (pts, ancho) in enumerate(trazos):
        p.talla(pts, ancho=ancho, punta=(.95, .25), temblor=1.1, semilla=i * 5 + 2)

    # Los nudos, solo en los dos culmos de delante: en los del fondo se leían
    # como manchas sueltas a la mitad del tamaño real.
    for x, y, w in ((80, 118, 6.5), (84, 74, 6.0), (124, 116, 6.5), (118, 72, 6.0)):
        p.talla([(x - w, y), (x + w, y - 1)], ancho=4.0, punta=(.85, .85), temblor=.3)

    # Follaje: pares de hojas colgando del cruce. Van en la mitad alta y hacia
    # afuera, que es como se abre la copa.
    for x, y, dx, dy in ((118, 34, 32, -14), (86, 40, -30, -16), (136, 58, 28, 8),
                         (66, 60, -26, 4), (100, 20, 10, -18)):
        p.talla([(x, y), (x + dx, y + dy)], ancho=3.0, punta=(.6, 0), temblor=.5)
    return p


def dibujo_culmo():
    """Un tramo de caña con su nudo y la cota del corte. — EL CULMO.

    El plano medio: la cámara ya bajó del dosel y tiene delante una caña sola.
    El dibujo dice dónde se corta —por encima del nudo— y lo dice con una cota,
    no con un tajo: un tajo dibujado es un golpe dado, y esto es la regla que
    se sigue antes de darlo.

    Va sin número, como todas las cotas de este generador: la edad la pone el
    guadual, y aquí no se inventan datos.
    """
    p = Plancha(VW, VH, "Tramo de culmo de guadua con su nudo y la cota de corte")

    x, corte = 84, 74
    # El culmo entra y sale del cuadro: el encuadre corta, como en el dosel.
    _culmo(p, x, 0, VH, ancho=13, nudos=(corte + 24, 148), punta=(.98, .98), temblor=.9)
    # El nudo de referencia, más marcado que los otros dos: es el que manda.
    p.talla([(x - 17, corte + 24), (x + 17, corte + 23)], ancho=7.5, punta=(.9, .9), temblor=.3)

    # La cota del corte: línea de trazos a la altura donde entra el filo, un
    # canuto por encima del nudo. A trazos y no maciza —es una indicación, no
    # una pieza— y con el aspa de las otras cotas en el extremo libre.
    for x0 in (108, 126, 144):
        p.talla([(x0, corte), (x0 + 12, corte)], ancho=3.4, punta=(.5, .5), temblor=.25)
    p.talla([(x - 20, corte), (x + 22, corte)], ancho=4.4, punta=(.9, .3), temblor=.3)
    p.talla([(160, corte - 9), (170, corte), (160, corte + 9)],
            ancho=3.0, punta=(.15, .15), temblor=.3)
    return p


def dibujo_rizoma():
    """El rizoma bajo la línea de tierra, con sus yemas y el brote. — EL SUELO.

    El plano que la cámara no puede tener: lo que hay debajo. Es el que explica
    los otros dos —por qué cortar una caña no mata el guadual— y por eso es el
    último, cuando la secuencia ya llegó al suelo.

    La tierra va HACHURADA y no entintada. Es la única vez que la regla de la
    masa no aplica: entintado, el terreno se comía el rizoma —los dos son el
    mismo crema, así que una masa maciza no lo contiene, lo tapa— y quedaba un
    ladrillo con dos cañas encima. Hachurada, la trama dice «esto es tierra» y
    el rizoma se lee dentro de ella, que es todo el dibujo.
    """
    p = Plancha(VW, VH, "Rizoma de guadua bajo tierra, con sus yemas y un brote nuevo")

    tierra = 96

    # ── Lo que está fuera: el tocón de la caña cortada y el brote nuevo.
    _culmo(p, 58, 30, tierra, ancho=11, nudos=(62,), punta=(.98, .95))
    p.talla(arco(58, 32, 12, 4.5, 0, 360, 20), ancho=4.0, punta=(1, 1), temblor=.35)
    _culmo(p, 140, 34, tierra, ancho=7.5, nudos=(70,), punta=(.9, 0), temblor=1.0)
    for y, s in ((72, 1), (52, -1)):
        p.talla([(140, y + 6), (140 + 26 * s, y - 12)], ancho=4.2, punta=(.8, 0), temblor=.5)

    # ── La línea de tierra: recta y de lado a lado. Esto es una sección, no un
    # paisaje.
    p.talla([(0, tierra), (VW, tierra + 2)], ancho=4.2, punta=(1, 1), temblor=1.2)
    # Y la trama del terreno: tajos cortos y paralelos, como se sombrea una
    # sección en una lámina. Se saltan la banda del rizoma —de 118 a 158— para
    # no cruzarlo; una trama que le pasa por encima lo convierte en textura.
    for x in range(10, VW, 17):
        for y, largo in ((tierra + 9, 12), (170, 12)):
            if 118 < y < 158:
                continue
            p.talla([(x, y), (x - 6, y + largo)], ancho=2.4, punta=(.35, .35),
                    temblor=.3, semilla=x + y)

    # ── El rizoma. Va en negativo sobre la masa —el mismo crema del resto—,
    # así que se lee como lo que es: la parte viva dentro de la tierra.
    p.talla([(22, 150), (58, 128), (104, 124), (150, 134), (182, 152)],
            ancho=12, punta=(.35, .35), temblor=1.0)
    # Las yemas: los dos culmos de arriba nacen de ella, y quedan dos más sin
    # brotar. Eso es el dibujo entero —de aquí sale el siguiente—.
    p.talla([(58, 128), (58, tierra + 2)], ancho=9, punta=(.9, .95), temblor=.5)
    p.talla([(140, 133), (140, tierra + 2)], ancho=7, punta=(.9, .95), temblor=.5)
    for x, y in ((88, 124), (168, 143)):
        p.talla([(x, y), (x + 3, y - 16)], ancho=6, punta=(.85, .1), temblor=.4)
    # Raíces, cortas y hacia abajo: sostienen la lectura de que esto está
    # enterrado sin robarle el sitio al rizoma.
    for x, dx in ((44, -12), (76, -6), (110, 4), (154, 12)):
        p.talla([(x, 150), (x + dx, 176)], ancho=3.4, punta=(.5, 0), temblor=.6)
    return p


# Los tres hitos de «Por qué guadua». Carpeta aparte y viewBox propio: ver la
# nota de arriba. No se mezclan con los del calificador —allí un dibujo dice qué
# necesitas, aquí dicen cómo vive el material— ni con los de obra.
DIBUJOS_VIDA = {
    "brote": dibujo_brote,
    "corte": dibujo_corte,
    "cubierta": dibujo_cubierta,
}

# Los tres planos del cierre de la portada. Carpeta propia por la misma razón
# que los de obra y los de la vida: no comparten celda con nadie y no dicen lo
# mismo que ningún otro grupo.
DIBUJOS_CIERRE = {
    "dosel": dibujo_dosel,
    "culmo": dibujo_culmo,
    "rizoma": dibujo_rizoma,
}

if __name__ == "__main__":
    import pathlib

    destino = pathlib.Path(__file__).resolve().parent.parent / "web/src/components/ilustraciones"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "obra").mkdir(exist_ok=True)
    (destino / "panel").mkdir(exist_ok=True)
    (destino / "vida").mkdir(exist_ok=True)
    (destino / "cierre").mkdir(exist_ok=True)
    iconos = destino.parent / "iconos"
    iconos.mkdir(parents=True, exist_ok=True)
    for carpeta, grupo in ((destino, DIBUJOS), (destino / "obra", DIBUJOS_OBRA),
                           (destino / "panel", DIBUJOS_PANEL),
                           (destino / "vida", DIBUJOS_VIDA),
                           (destino / "cierre", DIBUJOS_CIERRE), (iconos, DIBUJOS_ICONO)):
        for nombre, hacer in grupo.items():
            ruta = carpeta / f"{nombre}.svg"
            ruta.write_text(hacer().svg() + "\n")
            print(f"{ruta.relative_to(destino.parents[4])}  {ruta.stat().st_size // 1024} KB")
