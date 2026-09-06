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


def gubia(puntos, ancho=6, semilla=0, punta=(0.0, 0.0), temblor=1.0, n=None):
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

    contorno = izq + der[::-1]
    d = f"M{contorno[0][0]:.1f} {contorno[0][1]:.1f}"
    for x, y in contorno[1:]:
        d += f"L{x:.1f} {y:.1f}"
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

    def __init__(self, ancho, alto, titulo):
        self.w, self.h, self.titulo = ancho, alto, titulo
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
        d = gubia(puntos, **kw)
        (x0, y0), (x1, y1) = puntos[0], puntos[-1]
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        self.paths.append(
            f'<g class="gu" style="--x:{x0:.0f}px;--y:{y0:.0f}px;'
            f'--a:{ang:.0f}deg;--i:{self._n}"><path d="{d}"/></g>'
        )
        return self

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
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'fill="currentColor" role="img" aria-label="{self.titulo}">'
            f"{cuerpo}</svg>"
        )


# ── Los dibujos ───────────────────────────────────────────────────────────
#
# Los tres tienen el mismo viewBox: en el visor del calificador las vistas se
# apilan en la misma celda de la rejilla, y si un dibujo fuera más alto que
# otro el panel saltaría al cambiar de opción.

W, H = 420, 260


def dibujo_construccion():
    """Pórtico completo: pedestal, columna, cercha y cubierta.

    Es el apunte que ya estaba escrito debajo —«del pedestal a la cubierta»—
    pasado a dibujo. El pedestal va como masa entintada y no como trazo: es lo
    único de la escena que no es guadua, y el contraste de técnica lo dice sin
    necesidad de rótulo.
    """
    p = Plancha(W, H, "Pórtico en guadua: pedestal, columna, cercha y cubierta")
    suelo, cordon, apex = 224, 128, 46

    p.talla([(44, 84), (210, apex - 6), (376, 84)], ancho=9, punta=(.9, .9), temblor=1.1)
    p.talla([(72, cordon), (210, apex + 9)], ancho=6, punta=(.85, .35), temblor=.9)
    p.talla([(348, cordon), (210, apex + 9)], ancho=6, punta=(.85, .35), temblor=.9)
    p.talla([(72, cordon), (348, cordon)], ancho=6.5, punta=(.85, .85), temblor=1.2)
    p.talla([(210, apex + 14), (210, cordon - 2)], ancho=4.2, punta=(.35, .8))
    p.talla([(146, 89), (206, cordon - 4)], ancho=3.4, punta=(.35, .6), temblor=.6)
    p.talla([(274, 89), (214, cordon - 4)], ancho=3.4, punta=(.35, .6), temblor=.6)

    for x in (88, 332):
        p.talla([(x, cordon + 3), (x, suelo - 8)], ancho=8.5, punta=(.9, .95), temblor=.9)
        for y in (158, 192):  # nudos
            p.talla(arco(x, y, 10, 3.4, 205, 335), ancho=3.4, punta=(.3, .3), temblor=.3)
        p.masa(f"M{x-19} {suelo+9}L{x-13} {suelo-9}L{x+13} {suelo-9}L{x+19} {suelo+9}Z")

    p.talla([(56, suelo + 16), (364, suelo + 16)], ancho=3.4, punta=(0, 0), temblor=1.4)
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

if __name__ == "__main__":
    import pathlib

    destino = pathlib.Path(__file__).resolve().parent.parent / "web/src/components/ilustraciones"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "obra").mkdir(exist_ok=True)
    iconos = destino.parent / "iconos"
    iconos.mkdir(parents=True, exist_ok=True)
    for carpeta, grupo in ((destino, DIBUJOS), (destino / "obra", DIBUJOS_OBRA),
                           (iconos, DIBUJOS_ICONO)):
        for nombre, hacer in grupo.items():
            ruta = carpeta / f"{nombre}.svg"
            ruta.write_text(hacer().svg() + "\n")
            print(f"{ruta.relative_to(destino.parents[4])}  {ruta.stat().st_size // 1024} KB")
