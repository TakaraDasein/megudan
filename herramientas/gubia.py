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


def gubia(puntos, ancho=6, semilla=0, punta=(0.0, 0.0), temblor=1.0, n=26):
    """Un trazo de gubia como path cerrado.

    `puntos`  línea media, en coordenadas del viewBox.
    `ancho`   grosor máximo, en el centro del trazo.
    `punta`   grosor relativo en cada extremo (0 = afilado, 1 = a tope).
              Un culmo cortado a escuadra termina en 1; una talla libre en 0.
    `temblor` cuánto se desvía del trazo ideal.
    """
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
        self._n += 1
        kw.setdefault("semilla", self._n)
        self.paths.append(gubia(puntos, **kw))
        return self

    def masa(self, d):
        """Mancha entintada literal, sin pasar por la gubia."""
        self.paths.append(d)
        return self

    def svg(self):
        cuerpo = "".join(f'<path d="{d}"/>' for d in self.paths)
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


DIBUJOS = {
    "portico": dibujo_construccion,
}

if __name__ == "__main__":
    import pathlib

    destino = pathlib.Path(__file__).resolve().parent.parent / "web/src/components/ilustraciones"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, hacer in DIBUJOS.items():
        ruta = destino / f"{nombre}.svg"
        ruta.write_text(hacer().svg() + "\n")
        print(f"{ruta.relative_to(destino.parents[4])}  {ruta.stat().st_size // 1024} KB")
