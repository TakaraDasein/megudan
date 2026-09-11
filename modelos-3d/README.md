# Modelos 3D

Todo lo que produce los kioscos que giran en el sitio: los archivos de origen y
el histórico de secuencias que se han ido publicando.

Lo que el sitio sirve vive en `web/public/`, no aquí. Esta carpeta es el taller
y el archivo: de aquí sale lo que se publica, y aquí queda lo que se reemplazó.

```
modelos-3d/
├── blender/            los .blend de origen
└── secuencias/         histórico, una carpeta por versión publicada
    ├── sumak/
    ├── teja/
    └── paja/
```

## Los tres modelos

Son tres edificios distintos, no tres vistas del mismo. El visor
(`web/src/components/Giratorio.astro`) los elige por nombre.

| nombre  | qué es | origen | se sirve en |
|---------|--------|--------|-------------|
| `sumak` | kiosco del Restaurante Sumak: cinco conos de guadua con cubierta de paja sobre basas de concreto | render propio, desde `blender/kiosco-sumak.blend` | `web/public/modelo-360/` |
| `teja`  | octogonal de teja de barro con barandas | vídeo generado, `fuentes-video/kiosco-360.mp4` | `web/public/kiosco-teja-360/` |
| `paja`  | cónico de techo de paja y columnas en celosía | vídeo generado | `web/public/kiosco-paja-360/` |

**Solo `sumak` se puede volver a renderizar.** Los otros dos salen de vídeos
generados y no hay modelo detrás: lo que hay en `secuencias/` es todo lo que
existe de ellos. Si hay que rehacerlos, se rehace el vídeo.

## Cómo se regenera `sumak`

```bash
# 1 · los fotogramas, desde el modelo de Revit
blender -b modelos-3d/blender/kiosco-sumak.blend \
        --python herramientas/render-kiosco-360.py -- \
        --motor cycles --fotogramas 72 --ancho 1180 --alto 885 \
        --salida /tmp/kiosco-72

# 2 · recorte al encuadre común y WebP con alfa
python3 herramientas/empacar-360.py /tmp/kiosco-72 web/public/modelo-360
```

Antes de sobrescribir `web/public/modelo-360/`, **copia lo que había** a una
carpeta nueva en `secuencias/sumak/`. Ese es el motivo de que esta carpeta
exista: durante el desarrollo se perdieron un par de versiones al regenerar
encima, y sin el original no hay forma de comparar si un cambio de material
mejoró algo o solo lo cambió.

Para tantear sin gastar diez minutos, `--motor eevee` y `--angulos 0,90,250`
sacan tres vistas sueltas en segundos. Los parámetros de luz y material están
documentados en la cabecera del script y en `CLAUDE.md`.

## Los dos de vídeo

Salen de `herramientas/extraer-secuencia.sh` (croma, recorte común y WebP) y
después de `herramientas/desflecar-360.py`, que les quita el halo gris del
borde: al neutralizar el verde del croma en los píxeles de borde, `despill` los
deja lavados, y sobre el guadual eso se ve como escarcha alrededor de las
columnas.

## Nombres de las carpetas de versión

`vN-qué-cambió-fotogramas`, por ejemplo `v3-luz-suave-72`. El número ordena y el
resto dice por qué existe; una fecha sola no responde la pregunta que uno se
hace al abrir esto seis meses después.
