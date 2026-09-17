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
    ├── paja/
    └── culmo/          NO se publica hoy — ver más abajo
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


## `culmo/` — el recorte del brote, archivado y sin usar

**No se sirve nada de esto.** Está aquí porque costó averiguarlo y porque la
próxima vez que alguien tenga la idea conviene que encuentre el resultado en
lugar de repetir el camino.

### Qué es

El descenso del guadual (`VidaGuadual.astro`) no puede tener paralaje de verdad:
el sujeto está horneado en los 72 fotogramas, así que mover el fondo mueve
también la caña. Esto son esos mismos fotogramas con el culmo recortado y alfa
alrededor — la capa que haría falta para separarlo en planos.

Se montó, se vio en el sitio y **se descartó por criterio visual**, no porque
fallara. El código que lo usaba se retiró de `VidaGuadual.astro` y de
`motion.ts`; lo que quedó vivo del mismo trabajo es el empuje del lienzo
(`scale` 1 → 1.06) y el paralaje de los kioscos, que sí son capas de verdad.

### Las tres versiones, y qué enseña cada una

| | motor | fiables | qué aprendió |
|---|---|---|---|
| `v1` | GrabCut propagado | 25 | La máscara engorda ×3 y acaba conteniendo una columna de bosque: la cobertura pasa de 6,7 % a 20,5 % y ahí se estanca |
| `v2` | rembg `u2net` | 18 | Silueta correcta, pero el modelo **excluye las púas** por su cuenta: bajar el umbral no las recupera |
| `v3` | rembg `u2net`, alfa blando | 18 | Umbral bajo y sin apertura morfológica; mejora el filo pero las púas siguen sin estar, porque no están en el alfa |

Lo que **no** llegó a versión: `isnet-general-use` sí captura las púas, pero
deja el cuerpo semitransparente. La combinación —cuerpo de `u2net`, púas de
`isnet`, unidas por el máximo dentro de una banda dilatada alrededor del
cuerpo— se probó y funcionaba. Ahí se paró.

### Dos cosas que conviene no volver a descubrir

- **El brote y la hojarasca son el mismo marrón**, a la misma distancia y con la
  misma luz. No hay color, ni foco, ni forma que los separe: hace falta
  segmentación semántica. La visión clásica no llega, y afinarla no es cuestión
  de parámetros.
- **rembg falla de golpe, no degradando.** En el fotograma 18 devuelve un jirón
  del 1,6 % porque ahí el sujeto deja de ser un objeto —un brote entero— y pasa
  a ser un tramo de caña que entra y sale del encuadre. Por eso
  `recortar-culmo.py` lleva una guarda de continuidad que compara cada máscara
  con la última aceptada (salto de cobertura y solape) y corta el tramo
  publicable en el primero que se rompe. El tramo es un **prefijo**: no se
  reanuda aunque los siguientes salgan bien, porque un hueco en medio se ve como
  un parpadeo.

### Cómo se regenera

```bash
# rembg no es dependencia del proyecto: es de la máquina, y el script cae a
# GrabCut si no está.
pip install rembg onnxruntime

python3 herramientas/recortar-culmo.py --version v4          # segmenta y archiva
python3 herramientas/recortar-culmo.py --version v4 \
        --solo-publicar --publicar 18                        # y deja los buenos servidos
```

`--solo-publicar` existe porque segmentar son 72 pasadas del modelo y republicar
es solo recortar y recomprimir: afinar el peso no debería obligar a rehacer las
máscaras ni a inventar una versión nueva.

**Si vuelve a publicarse**, dos cosas que costaron una vuelta cada una:

- El recorte tiene que llevar **el mismo `filter` que el lienzo**. Sale de
  `web/public/secuencia/`, que son los fotogramas CRUDOS: en escritorio el
  virado lo pone el CSS. Sin él se ve más claro y más contrastado que el fondo
  del que se recortó, o sea pegado encima.
- Y en móvil sería al revés: allí el lienzo va con `filter: none` porque el
  virado viene horneado en `secuencia-movil/`, así que un recorte para esa
  pantalla necesitaría el virado horneado también.
