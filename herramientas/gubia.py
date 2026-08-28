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


DIBUJOS = {
    "portico": dibujo_construccion,
    "atado": dibujo_suministro,
    "union": dibujo_asesoria,
}

if __name__ == "__main__":
    import pathlib

    destino = pathlib.Path(__file__).resolve().parent.parent / "web/src/components/ilustraciones"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, hacer in DIBUJOS.items():
        ruta = destino / f"{nombre}.svg"
        ruta.write_text(hacer().svg() + "\n")
        print(f"{ruta.relative_to(destino.parents[4])}  {ruta.stat().st_size // 1024} KB")
