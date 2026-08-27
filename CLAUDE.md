# Megudan — landing y portafolio en guadua

Sitio para Megudan Construcciones Sostenibles (Colombia). Reemplaza un sitio Wix
anterior. El objetivo de cada pantalla es la misma: llevar a una conversación por
WhatsApp ya calificada.

## Gestor de paquetes: pnpm, y solo pnpm

**Usa `pnpm` siempre. Nunca `npm` ni `yarn` ni `npx`.**

```bash
cd web
pnpm install
pnpm dev        # http://localhost:4321
pnpm build      # estático en dist/
pnpm preview    # sirve dist/ ya compilado
pnpm dlx <pkg>  # en lugar de npx
```

Para el servidor de desarrollo, prefiere el modo en segundo plano — así no
bloquea la sesión:

```bash
pnpm exec astro dev --background   # y luego: astro dev stop | status | logs
```

`npm install` está bloqueado por un `preinstall` con `only-allow`, pero no
confíes en el guardia: no ejecutes npm en primer lugar. Un `package-lock.json`
en este repo es un error — bórralo.

Detalles que importan y no son obvios:

- **`pnpm-workspace.yaml` en `web/` es obligatorio.** Existe un
  `pnpm-workspace.yaml` en `$HOME` de esta máquina. Sin el ancla local, pnpm sube
  por el árbol, adopta el de `$HOME` y `pnpm install` **no instala nada**: dice
  "Already up to date" y termina en éxito. Si ves ese mensaje con `node_modules`
  ausente, ese es el motivo.
- **Los scripts de build van en `allowBuilds`** dentro de `pnpm-workspace.yaml`.
  pnpm 11 usa ese campo, no `onlyBuiltDependencies` (que es de pnpm 10 y quedó
  ignorado en silencio). `sharp` y `esbuild` lo necesitan; sin ellos el build
  falla al procesar imágenes.
- **El build en frío puede quedarse sin memoria.** Cuando hay variantes de
  imagen nuevas que generar —y más si el servidor de desarrollo está
  encendido—, `pnpm build` muere con «heap out of memory». Para la primera
  pasada: `pnpm exec astro dev stop` y
  `NODE_OPTIONS=--max-old-space-size=8192 pnpm build`. Con la caché caliente
  vuelve a compilar en segundos sin nada de eso. Si el CI hace build limpio,
  ahí hay que subir el heap.
- `.npmrc` fija `shamefully-hoist=true` porque Astro y Vite resuelven mejor con
  `node_modules` plano que con los enlaces estrictos de pnpm.

## Arquitectura

Lee `../ARQUITECTURA.md` antes de cambiar estructura o diseño. Resumen:

- **Astro con islas.** Todo es HTML estático. Hay dos islas React, las dos con
  `client:visible`, y no debería haber una tercera sin una razón igual de
  concreta que las suyas:
  - `islands/Calificador.tsx` — el embudo a WhatsApp.
  - `islands/MuroProyectos.jsx` — el muro de obra de la portada. Es
    `DriftWall` de React Bits, vendorizado: el cuerpo se deja igual que
    upstream (clases y nombres en inglés) para poder compararlo cuando salga
    versión nueva, y lo de Megudan va aparte, numerado en la cabecera del
    archivo. Existe como isla porque vive del puntero y de un bucle `rAF`.
    Su envoltorio es `components/MuroObra.astro`.
- **Una fuente de verdad por dato**: `web/src/data/sitio.ts` (contacto,
  servicios), `web/src/content/proyectos/*.md` (obra),
  `web/src/data/productos.json` (catálogo).
- **Toda conversión pasa por `enlaceWhatsApp()`** en `sitio.ts`. No construyas
  URLs de `wa.me` a mano en ningún componente.
- **Dos páginas, dos públicos.** `/` es para quien va a construir;
  `/comprar-guadua` para quien va a comprar material. No devuelvas el catálogo
  ni el proceso de curado a la portada: se separaron a propósito.

  La bifurcación se resuelve en el primer segundo con `ConmutadorRama.astro`,
  que va en las dos portadas. Son **enlaces reales**, no pestañas de JS: sin
  JavaScript siguen funcionando y cada rama conserva su URL y su SEO. Si le
  pones `transition:name` al carril entero en vez de al señalador, el navegador
  captura el grupo como una imagen y el deslizamiento de dentro se pierde.

- **El sitio navega con `<ClientRouter />`** (View Transitions), declarado en
  `Base.astro`. Dos consecuencias que muerden:
  - El módulo de un `<script>` se evalúa **una sola vez**, pero el DOM se
    sustituye en cada navegación. Por eso `iniciarMovimiento()` se rearma en
    `astro:page-load` y se desmonta en `astro:before-swap`; si no, los
    ScrollTrigger quedan apuntando a nodos que ya no existen.
  - `astro:after-swap` se dispara **antes** de que corran las animaciones de la
    transición, no después. No lo uses para limpiar nada de lo que dependa una
    animación: la mata al arrancar.
- **Los fotogramas de `public/secuencia/` no se editan a mano.** Se generan con
  `herramientas/extraer-secuencia.sh` desde `fuentes-video/guadual.mp4`, y el
  reparto por movimiento es lo que permite que el mapeo scroll→fotograma sea
  lineal. Si los reemplazas por otros repartidos por tiempo, el barrido de la
  portada se siente trabado al principio y apurado al final.
- **Usa `<Image>` de `astro:assets`, nunca `<img>` con `src` crudo.** Hay fotos
  duplicadas byte a byte entre proyectos y productos; Astro las deduplica y un
  `<img>` crudo puede apuntar a un archivo que nunca se emite (404).
- **El color es el del manual de marca**, no una paleta inventada ni muestreada
  de fotos. Los seis colores están en `web/src/styles/tokens.css` con su origen
  documentado. Ojo: los hex impresos en el PDF del toolkit están mal —el
  diseñador repitió dos valores en pares de swatches—; los buenos son los que
  están en `tokens.css`, muestreados de los rellenos reales.

  Tres trabajos, y solo tres: **naranja = acción** (`--accion` para rellenos,
  `--accion-tx` para texto y bordes, que el naranja puro no pasa contraste sobre
  `--s2`), **café guadua = dato** (`--cruda`), **verde oliva = estructura**
  (`--estructura`, índices y numeración). No introduzcas colores nuevos.

- **El logo no se dibuja con texto.** Está en `web/public/marca/` como SVG
  extraído del `.ai` original, y se usa con `<img>` —la única excepción a la
  regla de `<Image>`, porque no hay duplicados que deduplicar y así se cachea
  una vez en lugar de incrustar 466 trazos en cada página—. El lema de marca
  («Lugares que respiran contigo») vive en `sitio.ts` y va en versalitas
  espaciadas y en naranja, encima del titular, como lo firma el manual.

- **Tipografía pendiente.** El manual pide Condor y The Seasons; ninguna de las
  dos está en Google Fonts ni vino con licencia web. El sitio sigue con
  Archivo/Fraunces/Inter hasta que el cliente envíe los `.woff2`. El cambio está
  aislado en `tokens.css`.
- **Los tipos de corte son la lámina «Meso» del manual**, en
  `web/src/components/TiposDeCorte.astro`. Las cuatro ilustraciones son WebP con
  alfa y no SVG a propósito: el vector que sale del `.ai` trae cada marca como
  un contorno de ~1126 puntos —117 KB comprimidos entre las cuatro— y diezmarlo
  facetaba las elipses. A 460 px, en crema y sobre superficie fija, el mapa de
  bits pesa 30 KB y se ve mejor. Los nombres (boca de pescado, transversal, a
  bisel, pico de flauta) son los del manual: no los cambies ni inventes otros.

- **Animación por atributo**, en `web/src/lib/motion.ts`: `data-revelar-texto`,
  `data-entrada`, `data-parallax`. Respeta `prefers-reduced-motion`.

- **Un solo radio para todo el sitio**: `--borde`, en `tokens.css`, a 10 px.
  Gobierna botones, tarjetas, marcos e imágenes. Que sea uno solo no es pereza:
  dos radios distintos en la misma pantalla se notan enseguida.

- **El túnel de entrada a la obra se anima en el DOM**, no con la View
  Transition del router (`MuroProyectos.jsx`, cambio 4). Así existe en
  cualquier navegador tenga o no la API, y no depende de cuándo decida el
  router intercambiar la página. Dura 380 ms a propósito: por encima de unos
  400 la animación deja de leerse como respuesta al clic y empieza a leerse
  como espera.

## Contenido incompleto: es a propósito

`ubicacion`, `anio` y `area` aceptan `null` en el esquema, y los precios de
producto están vacíos. **No inventes esos datos ni los rellenes con ejemplos.**
El cliente aún no los ha entregado; lo que falta está en `contenido/PENDIENTES.md`.
La ficha técnica solo imprime los campos con valor, así que la página se ve
correcta mientras tanto.

Lo mismo con el sitio Wix anterior: gran parte de su contenido era relleno de
plantilla (dirección falsa en México, productos "Soy un producto", precios sin
unidad). No lo tomes como fuente de verdad. `assets-origen/` sí tiene las
fotografías reales en resolución original.

## Idioma

Todo el código, comentarios, nombres de variables, rutas y contenido van en
**español**. Es un sitio colombiano y lo mantiene un equipo hispanohablante.
