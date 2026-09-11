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
- **Al tocar `content.config.ts`, reinicia el servidor de desarrollo.** El
  esquema nuevo entra en caliente pero la caché de contenido no: las entradas
  quedan validadas contra el esquema viejo, las que ya no encajan **se caen de
  la colección en silencio** y `getCollection` devuelve menos de las que hay.
  El síntoma no parece de esquema —el muro de la portada dibuja una columna
  menos, porque su número de columnas es `proyectos.length`— y `pnpm build`
  sigue pasando, porque parte de cero. El error real está en
  `astro dev logs`, como `InvalidContentEntryDataError`. Se arregla con
  `astro dev stop`, `rm -rf .astro node_modules/.astro` y volver a arrancar.

- **Una fuente de verdad por dato**: `web/src/data/sitio.ts` (contacto,
  servicios), `web/src/content/proyectos/*.md` (obra),
  `web/src/data/productos.json` (catálogo).

  En obra, las fotos viven **solo** dentro de `secciones[]`, agrupadas por
  tramo. No hay una lista plana aparte: tener las dos se desincroniza al primer
  cambio. Quien necesite el montón —el muro de la portada— usa `fotosDe()` de
  `web/src/lib/obra.ts`.

  El título de un tramo no siempre es una etapa constructiva, y eso es
  deliberado. Solo tres de las cinco obras tienen fotos de proceso; el Puente y
  el Restaurante Sumak están fotografiados terminados, así que ahí los tramos
  son momentos del recorrido. Ponerles rótulo de etapa sería describir fotos
  que no existen. Si llegan fotos de montaje de esas dos, ahí sí se renombran.

  Los textos de tramo afirman **solo lo que se ve en la fotografía** —material,
  tipo de unión, secuencia de montaje—. Luces, cargas, especies y fechas están
  sin confirmar y no se inventan: van en `contenido/PENDIENTES.md`.

- **Un dibujo por obra**, en `web/src/components/ilustraciones/obra/`, elegido
  con el campo `ilustracion`. Va en la segunda columna de la cabecera, al lado
  del titular, y es el gesto que define esa obra: la cercha, el muro de tierra,
  la basa, el arco, el capitel. Se talla al abrir la página con la misma
  mecánica del calificador —`.gu`, `--x/--y/--a/--i`, 22 ms por gubia— y se
  queda quieto bajo `prefers-reduced-motion`.

  **Salen de `herramientas/gubia.py`, como los del calificador. No se editan a
  mano: se pisan en la siguiente pasada.** Para retocar uno se edita su
  `dibujo_*` y se corre `python3 herramientas/gubia.py`, que reescribe los tres
  del calificador y los cinco de obra. Son vaciados, no contornos: lo que no es
  guadua va como `masa` —la placa, la basa, los estribos, la piedra— y ese
  contraste de técnica dice el material sin rótulo.

  Los tres del calificador —`portico`, `atado`, `union`— **no se reusan en
  obra**: allí distinguen comprar de construir, y gastarlos en una ficha les
  quita ese trabajo. Por eso Casa Anolaima lleva la cercha sola y no el pórtico
  completo, que sería el dibujo del calificador con otro nombre.
- **Toda conversión pasa por `enlaceWhatsApp()`** en `sitio.ts`. No construyas
  URLs de `wa.me` a mano en ningún componente.
- **Una página, dos modos.** `/` es un solo documento que trae los dos públicos:
  el modo **construir** (`#construir`) para quien va a levantar algo y el modo
  **comprar** (`#comprar`) para quien va a comprar material. Cuál está en
  pantalla lo dice `data-modo` en el `<html>`.

  No mezcles las secciones de un modo con las del otro: el catálogo y el curado
  son del modo comprar, la obra y los servicios del modo construir, y esa
  separación es el punto. Los dos calificadores tampoco son el mismo —uno
  cotiza obra y el otro despacho—, aunque estén en el mismo archivo.

  Esto **era** dos páginas, `/` y `/comprar-guadua`, y se fundió a petición del
  cliente. Lo que se ganó es un cruce sin red de por medio; lo que se pagó está
  escrito para que nadie lo redescubra a golpes: la portada pesa 228 KB en vez
  de 176 KB con la mitad invisible en la primera visita, el SEO propio de la
  rama de compra se fundió en el de la portada, y sin JavaScript los dos modos
  salen apilados uno debajo del otro. `/comprar-guadua` sobrevive como
  redirección a `/#comprar` porque hay enlaces repartidos por fuera: **no la
  borres**.

  El conmutador es `ConmutadorRama.astro`, y va dentro de cada portada. Son
  **anclas reales** a los dos bloques, no botones de JS: con JavaScript el clic
  no navega —cambia el modo y anima el cruce—, y sin él siguen siendo lo que
  parecen. No le pongas `transition:name` al señalador: ya no hay navegación que
  animar, y con los dos conmutadores en el mismo documento dos elementos
  compartirían nombre de transición.

- **EL MODO INACTIVO SE DESPRENDE DEL DOM, no se oculta.** Es lo más importante
  de esta parte y lo más fácil de deshacer sin querer.

  Con `display: none` el bloque escondido seguía en el documento, así que
  `motion.ts` le creaba disparadores a todas sus secciones. Todas medían cero y
  estaban en la posición cero, luego todas cumplían su condición de entrada en
  el mismo instante; los de `descubrirImagenes` van con `once: true` y **se
  matan al cumplirse**, todos a la vez. Eso encoge el registro interno de
  ScrollTrigger mientras él lo recorre en su cascada de refresco, y revienta con
  `Cannot read properties of undefined (reading 'end')`. La excepción se lleva
  por delante el resto del rearme, y el síntoma no parece de esto: las secciones
  se quedan apagadas, «trabadas», sin nada en la consola que las relacione.

  El bloque inactivo se guarda aparte con un comentario ocupando su sitio —el
  orden importa, construir va primero—. Ver el script del modo en `Base.astro`.

- **Al cambiar de modo, el rearme de GSAP va al final, con la página quieta.**
  `getBoundingClientRect()` incluye las transformadas, así que rearmar mientras
  el plano viaja hace que ScrollTrigger mida el fotograma de la animación en vez
  de la página. Lo dispara `megudan:modo` cuando ya no queda una sola
  transformada puesta.

- **Cancela las animaciones por su referencia, nunca con `getAnimations()`.**
  Una animación de la Web Animations API no escribe estilos en línea: aplica su
  efecto por fuera del DOM. Las del cruce van con `fill: forwards`, así que su
  último fotograma sigue mandando después de terminar. Y al desprender el
  elemento sus animaciones dejan de ser «relevantes» —`getAnimations()` devuelve
  vacío— pero **siguen asociadas a él**, así que al reinsertarlo vuelven a
  aplicarse. Medido: el modo volvía ya corrido y a opacidad 0, sin un solo
  estilo en línea que lo explicara. Por eso se guardan las referencias y se
  cancelan antes de desprender.

- **El sitio navega con `<ClientRouter />`** (View Transitions), declarado en
  `Base.astro`, y eso vale ya solo para las fichas de obra: el cruce entre modos
  no es una navegación. Tres consecuencias que muerden:
  - El módulo de un `<script>` se evalúa **una sola vez**, pero el DOM se
    sustituye en cada navegación. Por eso `iniciarMovimiento()` se rearma en
    `astro:page-load` y se desmonta en `astro:before-swap`; si no, los
    ScrollTrigger quedan apuntando a nodos que ya no existen.
  - **Lo que vive en el `<html>` se pierde en el swap.** El router sustituye los
    atributos del `<html>` por los del documento entrante, y los `<script>` del
    `<head>` no se reejecutan. `data-modo` se escribe antes de pintar y hay que
    reponerlo después de cada navegación (`fijarModo`); sin eso, volviendo de
    una ficha de obra el modo llegaba indefinido, se desprendían **los dos**
    bloques y la portada quedaba en blanco.
  - `astro:after-swap` se dispara **antes** de que corran las animaciones de la
    transición, no después. No lo uses para limpiar nada de lo que dependa una
    animación: la mata al arrancar.

- **Al router no le queda nada que animar.** Su transición está en corte seco
  (`0.01ms`) en `global.css`, a propósito. Componer dos instantáneas a pantalla
  completa fue lo que ensuciaba el cruce: apagando las dos capas a la vez asoma
  el fondo entre ellas, y sumándolas con `plus-lighter` —lo que el navegador
  hace por defecto— el texto de la que sale se suma sobre la que entra si van
  desplazadas, y salen letras fantasma y manchas claras. Todo el movimiento de
  este sitio se anima en el DOM.
- **El kiosco que gira en la portada sale de Blender, no de un video.**
  `public/modelo-360/` son 72 fotogramas de un turntable renderizado con
  `herramientas/render-kiosco-360.py` desde
  `modelos-3d/blender/kiosco-sumak.blend`, y `herramientas/empacar-360.py` los
  recorta y los pasa a WebP con alfa. Para rehacerlos hay que correr los dos,
  en ese orden; no se editan a mano.

  **El taller está en `modelos-3d/`** —los `.blend` y el histórico de
  secuencias publicadas—, con su propio README. No entra a git por lo mismo que
  `assets-origen/`: material de origen, pesado y ya derivado en `web/public/`.
  **Antes de regenerar una secuencia, archiva la anterior ahí.** Durante el
  desarrollo se perdieron un par de versiones al renderizar encima, y sin la
  anterior no hay forma de saber si un cambio de material mejoró algo o solo lo
  cambió.

  Son 72 y no 36 porque el hero lo gira solo: a 36 pasos son 10° de salto y una
  vuelta pausada se ve escalonada. Los fotogramas se pagaron con resolución
  —el encuadre bajó de 1275 a 1010 px, y el hero solo enseña 470 px CSS—, así
  que el peso apenas se movió. Los otros dos modelos siguen a 36, y a ellos
  **no** les pongas giro automático lento sin rehacerlos.

  El `.blend` del kiosco Sumak es una **exportación de Revit** y de ahí salen casi todas las
  decisiones del script: no trae un solo material y son 2348 objetos, de los
  cuales 2271 se llaman `MONTANTE 1` —cada guadua suelta—, así que los
  materiales se reparten **por familia de nombre**. Trae UVs, pero son las de la
  exportación y no sirven para colocar nada: todo es procedural. Y trae cinco
  objetos `Nivel …`, que son anotaciones de niveles; uno está a 30 m y estira la
  caja de 7,7 × 8,2 m a 25 × 30 m, con lo que el centro de giro cae fuera del
  edificio. Se borran antes de medir.

  Dos trampas ya pagadas, por si se retocan los materiales: el ruido procedural
  va sobre coordenadas **`Generated`** y no `Object` —las locales de Revit son de
  cientos de unidades, así que cualquier escala razonable queda sub-píxel y el
  render la promedia a gris liso: la cubierta parece lona y no parece un error—,
  y `S.cycles.device = 'GPU'` por sí solo **no usa la GPU**: en `blender -b` hay
  que elegir el backend en las preferencias o Cycles cae a CPU en silencio.

  **Lo enterrado se recorta, no se esconde** (`recortar_bajo_cota`). El modelo
  trae la cimentación completa, y en un render normal no se ve porque hay
  terreno encima; aquí no lo hay —el fotograma va recortado sobre fondo
  transparente—, así que las zapatas quedaban colgando en el aire bajo el
  edificio. Los cortes se tapan con `holes_fill`: sin eso los arcos quedan como
  tubos abiertos. Cuesta poco porque a la cota de trabajo solo cruzan 20
  objetos; los 2270 culmos están enteros por encima.

  **El kiosco se apoya en sus cinco basas y no en la placa** (`--suelo`, por
  omisión `dados`). La placa de concreto va fuera: sobre la fotografía del
  guadual era una losa blanca flotando, lo más claro del encuadre, y le quitaba
  la atención a la guadua. Quitarla y dejar las basas es además coherente con
  cómo cuenta el resto del sitio —lo que no es guadua va como masa: la placa, la
  basa, el estribo—.

  **No quites también las basas.** Está la opción (`--suelo nada`, que sube el
  corte a 0.32) y se probó: los culmos cortados en el aire se leen como muñones
  y la celosía queda colgando de nada. El corte deja de parecer un encuadre y
  pasa a notarse como mutilación. Las basas son lo que hace que el recorte se
  lea como apoyo.

  El otro efecto del recorte es que **arregló el encuadre**. Con las zapatas
  colgando, la unión de las 36 siluetas daba una relación de 1.277 y el hero
  pedía `3 / 2`; sin ellas da 1.489 y encaja sola. Ojo con esto al tocar
  geometría: el recorte común se calcula sobre las 36 siluetas, así que
  cualquier pieza espuria contamina la proporción de la secuencia entera.

  **La paja tiene su propio material y no una variante del genérico**
  (`material_paja`). La cubierta era lo que delataba el render: se leía como
  lona de plástico. El culpable no era el color ni el relieve sino el
  **especular** —el Principled trae IOR 1.5 y la cubierta devolvía el cielo en
  una lámina continua de brillo, que es lo que el ojo llama plástico—. Se
  arregla con IOR bajo y, sobre todo, con **rugosidad que varía**, que rompe el
  reflejo en manchas en vez de quitarlo. Sus hiladas van sobre la **posición en
  mundo** y no sobre `Generated` como el resto: la paja se instala en hiladas
  horizontales a cota constante, y una hilada cruza de una concha a la vecina
  sin enterarse de que son dos objetos. Y el relieve va en **dos escalas
  encadenadas** —la hilada y el grano del tallo—, porque una sola se lee como
  abolladura, un grano de 4 mm se lee como terciopelo y uno más fino desaparece.

  **Realismo y peso son la misma variable.** La fibra es ruido de alta
  frecuencia y el códec la paga: la cubierta lisa de la primera versión pesaba
  1,96 MB y esta pesa 3,04 MB. Por eso `empacar-360.py` comprime a calidad
  **70** y no a 82 como el resto del sitio; la medición está en su cabecera. Si
  se sube el detalle del material, esto sube otra vez.

  **LA LUZ LA DA EL CIELO, no las lámparas.** El cielo de Nishita trae el disco
  solar incrustado en la textura, y en esta escena es la fuente dominante con
  diferencia: apagando las dos lámparas —`--sol 0 --relleno 0`— el modelo sale
  prácticamente idéntico. Si subes `--sol` y no ves cambios, es por esto. Las
  lámparas son el ajuste fino; la escena se gobierna con `--cielo`, la
  elevación del cielo y la exposición.

  **El cielo va a 65° aunque el sol vaya rasante**, y los dos están desacoplados
  a propósito. A 6° —como estuvo— el domo no es un relleno: casi toda su luz
  sale de una banda de horizonte estrecha y naranja, en el acimut del sol. Con
  la cámara orbitando y el sol fijo, eso hacía que el modelo **latiera**: la
  luminancia media iba de 45 a 131 según el ángulo —tres veces— y en los
  fotogramas a contraluz la mediana caía por debajo de la del fondo. Medio
  turntable se hundía en la fotografía. A 65° el latido baja a 1,3×.

  Es incoherente físicamente —cielo de mediodía con rayo de las seis— y da
  igual: el fotograma va recortado sobre fondo transparente y no hay horizonte
  con el que comparar. **No toques esa elevación sin recalibrar `--cielo`**: la
  irradiancia del Nishita cambia con ella de forma muy poco lineal.

  **Dos cosas probadas que NO funcionan**, para no repetirlas:
  - *Apagar el disco solar* (`sun_disc = False`) y dejar que manden las
    lámparas. Suena a manual y sale peor: el contraste de volumen cae de 1,06 a
    0,54 y el color de las zonas claras de 0,41 a 0,28. El sol del Nishita viene
    con su atmósfera, así que su tono cálido y el azul del domo están calculados
    juntos; dos lámparas con colores puestos a mano no reproducen esa relación.
  - *La luz de relleno* (`--relleno`) para rescatar la celosía en penumbra. Sube
    su luminancia un 7 % y cuesta un 10 % de contraste general. Queda
    parametrizada y en 0.

  **Y una trampa de método**: estos fotogramas nunca se ven solos. Van sobre la
  fotografía del guadual, que es verde y oscura, y juzgarlos contra el fondo del
  visor de imágenes engaña en las dos direcciones. Usa
  `herramientas/hoja-contacto.py`, que los compone sobre la imagen real del hero
  con el mismo velo que le echa la portada. Más de una decisión de luz de esta
  sección se tomó mirando el fondo equivocado y hubo que rehacerla.

  El sol va **fijo en el mundo**, no solidario con la cámara. Con fondo
  transparente el contraluz no se lee como un cambio de hora —no hay horizonte
  con el que compararlo— sino como brillo en el canto de la paja.

  Por ser una vuelta completa, el hero lo llama con `vaiven={false}`. El modelo
  `paja` sigue con el vaivén porque los suyos vienen de un video generado que
  oscila (ver `contenido/PROMPT-modelo-360.md`, que ya solo aplica a ese).

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
