#!/usr/bin/env python3
"""
Talla el mapa del paso «¿A dónde va el despacho?».

Emite `web/src/components/ilustraciones/sur-huila.svg`: los municipios del sur
del Huila que Megudan atiende, con un punto por cabecera. **No se edita a mano**
—se pisa en la siguiente pasada—; para cambiar la cobertura se tocan `ZONAS` y
`CONTEXTO` de aquí y se vuelve a correr:

    python3 herramientas/mapa-despacho.py

Por qué un SVG generado y no una librería de mapas:

  Leaflet o MapLibre pintan un mapa de verdad —tiles por red, etiquetas y
  paleta de OpenStreetMap— dentro de un panel donde todo lo demás está tallado
  con la gubia del isotipo, y obligan a una tercera isla React para encender
  uno de cinco puntos que nunca hacen zoom ni se arrastran. Aquí la geografía
  es real pero el trabajo se hace una sola vez, al compilar: al navegador solo
  le llega un SVG de unos pocos KB, sin JavaScript y sin red.

Origen del dato: geoBoundaries gbOpen COL ADM2 (fuente DANE), CC BY 4.0. La
descarga se cachea en `herramientas/.cache/` y no entra al repo: lo que se
versiona es el SVG, que es lo que se publica.
"""

from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / '.cache' / 'col-adm2.geojson'
SALIDA = RAIZ / 'web' / 'src' / 'components' / 'ilustraciones' / 'sur-huila.svg'

FUENTE = (
    'https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData'
    '/gbOpen/COL/ADM2/geoBoundaries-COL-ADM2_simplified.geojson'
)

# Las cuatro zonas del calificador. `id` es lo que el visor enciende, y tiene
# que coincidir con el prefijo `zona:` de `data/calificadores.ts`.
#
# Bruselas no es municipio sino corregimiento de Pitalito: por eso comparte
# polígono con él y solo se distingue por el punto. Encenderla ilumina Pitalito
# entero, que es la verdad administrativa y además el gesto útil —dice «eso te
# queda dentro de nuestra casa»—.
ZONAS = [
    ('pitalito',    'Pitalito',    'Pitalito',    (-76.0500, 1.8539)),
    # Bruselas queda al suroccidente de Pitalito, sobre la vía a Mocoa.
    ('bruselas',    'Pitalito',    'Bruselas',    (-76.1950, 1.7520)),
    ('san-agustin', 'San Agustín', 'San Agustín', (-76.2700, 1.8800)),
    ('isnos',       'Isnos',       'Isnos',       (-76.2167, 1.9283)),
]

# Vecinos que solo enmarcan. Sin ellos las cuatro zonas flotan en el vacío y no
# se lee que son un bloque contiguo, que es justo lo que hay que entender.
CONTEXTO = [
    'Palestina', 'Acevedo', 'Timaná', 'Elías',
    'Oporapa', 'Saladoblanco', 'Suaza',
]

ANCHO = 420          # px del viewBox; el mismo max-width que los dibujos.
MARGEN = 10
# Grados (~130 m). No es solo cuánto detalle se ve: las cabeceras de San
# Agustín e Isnos están casi sobre el límite entre las dos —las separa el
# Magdalena—, y con una tolerancia gruesa el borde se corre lo suficiente para
# dejar un punto del lado del municipio vecino.
TOLERANCIA = 0.0012
# Los vecinos solo enmarcan: nadie va a mirar si su borde tiene un recodo más.
# Diezmarlos al triple ahorra más de un tercio del archivo sin que se note.
TOLERANCIA_MARCO = 0.0036


def descargar() -> dict:
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        print(f'descargando {FUENTE}')
        urllib.request.urlretrieve(FUENTE, CACHE)
    return json.loads(CACHE.read_text())


def anillos(geom: dict) -> list[list[tuple[float, float]]]:
    """Los contornos de un Polygon o MultiPolygon, sin los huecos interiores."""
    if geom['type'] == 'Polygon':
        return [[tuple(p) for p in geom['coordinates'][0]]]
    return [[tuple(p) for p in poly[0]] for poly in geom['coordinates']]


def dentro(punto: tuple[float, float], anillo: list[tuple[float, float]]) -> bool:
    x, y = punto
    hit = False
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:] + anillo[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def diezmar(pts: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    """Douglas–Peucker. Sin dependencias: son dos docenas de líneas."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    largo = math.hypot(dx, dy)
    peor, idx = 0.0, 0
    for i, p in enumerate(pts[1:-1], 1):
        if largo == 0:
            d = math.hypot(p[0] - a[0], p[1] - a[1])
        else:
            d = abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / largo
        if d > peor:
            peor, idx = d, i
    if peor <= tol:
        return [a, b]
    return diezmar(pts[:idx + 1], tol)[:-1] + diezmar(pts[idx:], tol)


def main() -> None:
    datos = descargar()
    quiero = {m for _, m, _, _ in ZONAS} | set(CONTEXTO)

    # Hay municipios homónimos en otros departamentos (Palestina también es de
    # Caldas), así que además del nombre se exige que caigan en el recuadro del
    # sur del Huila.
    piezas: dict[str, list[list[tuple[float, float]]]] = {}
    for f in datos['features']:
        nombre = f['properties']['shapeName']
        if nombre not in quiero:
            continue
        rs = anillos(f['geometry'])
        cx = sum(p[0] for r in rs for p in r) / sum(len(r) for r in rs)
        cy = sum(p[1] for r in rs for p in r) / sum(len(r) for r in rs)
        if not (-76.6 < cx < -75.6 and 1.5 < cy < 2.3):
            continue
        piezas[nombre] = rs

    faltan = quiero - piezas.keys()
    if faltan:
        raise SystemExit(f'no aparecen en el geojson: {sorted(faltan)}')


    todos = [p for rs in piezas.values() for r in rs for p in r]
    lon0, lon1 = min(p[0] for p in todos), max(p[0] for p in todos)
    lat0, lat1 = min(p[1] for p in todos), max(p[1] for p in todos)
    # Equirectangular con el meridiano corregido por la latitud media: a este
    # tamaño de recuadro nada se nota, y evita traer una librería de proyección.
    k = math.cos(math.radians((lat0 + lat1) / 2))
    escala = (ANCHO - 2 * MARGEN) / ((lon1 - lon0) * k)
    alto = round((lat1 - lat0) * escala + 2 * MARGEN)

    def proyectar(p: tuple[float, float]) -> tuple[float, float]:
        x = MARGEN + (p[0] - lon0) * k * escala
        y = MARGEN + (lat1 - p[1]) * escala
        return round(x, 1), round(y, 1)

    def diezmados(rs, tol=TOLERANCIA):
        return [r for r in (diezmar(r, tol) for r in rs) if len(r) >= 3]

    # Cada punto tiene que caer dentro de su municipio **ya diezmado**, que es
    # el que se ve: comprobarlo contra el contorno original deja pasar
    # justamente el caso que importa —el borde se movió al simplificar y el
    # punto quedó del otro lado—. Si el mapa va a mentir, que reviente aquí.
    for zid, muni, _, punto in ZONAS:
        if not any(dentro(punto, r) for r in diezmados(piezas[muni])):
            raise SystemExit(f'el punto de «{zid}» cae fuera de {muni} al diezmar')

    def trazo(rs: list[list[tuple[float, float]]], tol=TOLERANCIA) -> str:
        d = []
        for r in diezmados(rs, tol):
            xy = [proyectar(p) for p in r]
            d.append('M' + 'L'.join(f'{x} {y}' for x, y in xy) + 'Z')
        return ''.join(d)

    zonas_por_muni = {muni for _, muni, _, _ in ZONAS}
    linea = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {alto}" '
             f'fill="none" aria-hidden="true">']

    # Primero el marco: los vecinos van debajo para que las zonas se recorten
    # limpias encima.
    for nombre in CONTEXTO:
        linea.append(
            f'<path class="mun" d="{trazo(piezas[nombre], TOLERANCIA_MARCO)}"/>')
    for nombre in sorted(zonas_por_muni):
        linea.append(f'<path class="mun zona" data-muni="{nombre}" '
                     f'd="{trazo(piezas[nombre])}"/>')

    for zid, muni, rotulo, punto in ZONAS:
        x, y = proyectar(punto)
        # El rótulo sale hacia el lado con sitio: en la mitad derecha del
        # recuadro se ancla al final, o se saldría del viewBox.
        derecha = x > ANCHO * 0.55
        tx = x - 8 if derecha in (True,) else x + 8
        ancla = 'end' if derecha else 'start'
        linea.append(
            f'<g class="punto" data-punto="{zid}" data-muni="{muni}">'
            f'<circle class="halo" cx="{x}" cy="{y}" r="9"/>'
            f'<circle class="pin" cx="{x}" cy="{y}" r="3.5"/>'
            f'<text x="{round(tx, 1)}" y="{y - 9}" text-anchor="{ancla}">{rotulo}</text>'
            f'</g>'
        )

    linea.append('</svg>')
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text('\n'.join(linea) + '\n')
    print(f'{SALIDA.relative_to(RAIZ)} — {SALIDA.stat().st_size / 1024:.1f} KB, '
          f'{ANCHO}×{alto}')


if __name__ == '__main__':
    main()
