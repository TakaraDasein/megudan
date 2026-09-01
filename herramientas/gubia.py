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
