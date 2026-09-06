# Megudan — arquitectura de la fase 1

## Decisiones

**Astro con islas.** La página es HTML estático. Solo el calificador se envía como
JavaScript (`client:visible`: se hidrata cuando entra en pantalla, no antes). El
portafolio, el catálogo y el pie no llevan JS de framework.

**Una sola fuente de verdad por tipo de dato.**

| Dato | Vive en | Quién lo edita |
|---|---|---|
| Teléfono, WhatsApp, servicios | `web/src/data/sitio.ts` | desarrollador |
| Proyectos (ficha + galería) | `web/src/content/proyectos/*.md` | desarrollador, con datos del cliente |
| Productos | `web/src/data/productos.json` | desarrollador, con datos del cliente |

Sumar una obra es agregar un `.md` y su carpeta de fotos. No se toca ningún componente.

**Los nulos son deuda de contenido, no bugs.** El esquema de `content.config.ts`
acepta `ubicacion`, `anio` y `area` en `null`. La ficha técnica solo imprime los
campos que tienen valor, así que la página se ve correcta mientras el cliente
completa la información. Lo que falta está listado en `contenido/PENDIENTES.md`.

**WhatsApp es la única salida.** Todo enlace de conversión pasa por
`enlaceWhatsApp()` en `sitio.ts`, que codifica el mensaje. Cambiar el número es
cambiar una línea.

## Referencias aprobadas por el cliente

Cuatro sitios mostrados al cliente, y qué se tomó de cada uno:

| Referencia | Qué se tomó |
|---|---|
| [eladiodieste.com](https://www.eladiodieste.com/iglesia-de-cristo-obrero) | fotografía a sangre en bandas alternadas; el párrafo grande + anotación lateral |
| [mosaicist.com](https://www.mosaicist.com/) | segunda línea del titular en serif itálica; índices `/01 /02 /03` |
| [vaulk.com](https://vaulk.com/fr-FR) | ficha técnica como filas con marca `↘` y regla fina |
| [findrealestate.com](https://findrealestate.com/) | titular sobre imagen a todo el ancho |

Lo común a las cuatro: la fotografía nunca vive dentro de un contenedor con
márgenes. En este sitio, el portafolio y la portada van a sangre; el texto sí
respeta el contenedor de 1180 px. Ese contraste es la retícula del sitio.

## Paleta

Es la del manual de marca (`New/01.Branding/Toolkit_Megudan.ai`, lámina «Paleta de
colores»), muestreada de los rellenos reales del PDF a 150 dpi. **Los códigos hex
impresos junto a cada swatch en ese PDF están mal**: el diseñador repitió
`#b0aea5` y `#888365` en pares de muestras y ninguno coincide con el relleno que
acompaña. Los buenos son estos.

| Token | Hex | Nombre en el manual | Trabajo en la página |
|---|---|---|---|
| `--accion` | `#E05F25` | Naranja | **acción**, en relleno: el botón que lleva a conversación |
| `--accion-tx` | `#F28B5C` | — | el mismo tono aclarado, para texto y bordes sobre oscuro |
| `--accion-honda` | `#7E3517` | — | bordes y estados en reposo |
| `--cruda` | `#CE9E77` | Café Guadua | dato: medidas, precios, rótulos técnicos |
| `--estructura` | `#B8AD44` | Verde Oliva | estructura: índices de sección, marcas de ficha |
| `--tx` | `#DBD7B9` | Verde Blanco | texto principal |
| `--bg` / `--s2` | `#1D2316` / `#2F3421` | Negro Verde / Verde Oscuro | superficies |
| `--acento-tipo` | Fraunces itálica | — | una sola línea del titular, nada más |

Tres trabajos, y solo tres: si algo está en naranja se puede pulsar, si está en
café es un dato, si está en oliva ordena. El color nunca es decorativo.

`--accion-tx` existe porque el naranja de marca da 4.47:1 sobre el fondo y **falla
AA sobre `--s2`** (3.57:1). El naranja puro se queda para rellenos, donde el texto
encima va en `--bg`; en cuanto el naranja es texto o borde, se usa el aclarado.

Contraste verificado contra el fondo: `--accion-tx` 6.61:1, cruda 6.73:1,
estructura 6.98:1, texto principal 11.07:1. El tono más bajo (`--tx4`, 4.04:1) se
usa solo en rótulos monoespaciados, nunca en prosa.

La tipografía del manual —Condor y The Seasons— no está en Google Fonts ni vino
con licencia web en la entrega. El sitio sigue con Archivo/Fraunces/Inter hasta
que el cliente envíe los `.woff2`; el cambio está aislado en `tokens.css`.

## Elemento de diseño: el nudo

La guadua se lee por sus nudos, el anillo donde la caña se refuerza. Cada sección
del sitio abre con uno: una línea fina con un engrosamiento corto a la izquierda
(`.nudo` en `global.css`), en el rojizo de la guadua ya curada — la parte de la caña
que más oscurece con el tratamiento. Es el único adorno estructural de la página y
significa algo del material, no decora.

## Una página, dos modos

La portada bifurca en dos públicos que no quieren lo mismo. Quien va a construir
necesita ver obra; quien va a comprar material necesita ver piezas y precios.
Mezclarlos en una sola lectura obliga a los dos a desplazarse por lo que no les
sirve, así que **nunca están los dos en pantalla**.

Lo que sí comparten es el documento. `/` trae los dos juegos de secciones y el
modo activo lo dice `data-modo` en el `<html>`; el inactivo se desprende del DOM
—no se oculta— hasta que alguien lo pide. Esto era dos páginas, `/` y
`/comprar-guadua`, y se fundió a petición del cliente: el cruce se gana en que
no espera a la red, y se paga en peso de portada y en el SEO propio que tenía la
rama de compra. `/comprar-guadua` sigue viva como redirección a `/#comprar`.

**Modo construir (`#construir`) — quien va a construir**

| Sección | Qué cuenta |
|---|---|
| Portada | la obra terminada — la promesa |
| **Calificador** | **la conversación, apenas pasa la portada** |
| Manifiesto | por qué guadua |
| Servicios | qué se puede contratar |
| Obra | lo construido |

**Modo comprar (`#comprar`) — quien va a comprar material**

| Sección | Qué cuenta |
|---|---|
| Portada | material listo para despacho |
| **Calificador** | **cotización de material, en el mismo lugar** |
| **Tipos de guadua** | las cinco presentaciones, con ficha y cotización |
| **Curado** | **las cuatro etapas entre el corte y la obra** |
| Cierre | cotización por WhatsApp |

El orden del segundo modo es deliberado: primero se ve **qué** se vende,
después **por qué** el material de Megudan aguanta y el de la esquina no. El
proceso de curado es el argumento de venta, así que va después del catálogo, no
antes: quien todavía no sabe qué está comprando no tiene con qué comparar.

El botón «Quiero comprar guadua» de la portada ya no abre el calificador —
cambia al modo comprar.

El cruce entre modos se anima en el DOM, no con la View Transition del router:
el bloque que sale viaja como un plano mientras sus secciones se apagan
escalonadas encima, y el intercambio ocurre cuando ya no queda nada visible pero
el movimiento sigue en el aire. Va en el eje del conmutador —a comprar viaja a
la derecha, a construir a la izquierda—, porque un conmutador es reversible y si
los dos sentidos se ven iguales no se sabe si se avanzó o se volvió.

## El calificador, un componente y dos juegos de preguntas

`components/islands/Calificador.tsx` no trae preguntas propias: las recibe. Los
dos juegos viven en `data/calificadores.ts`, y en los dos modos el calificador
va **inmediatamente después de la portada**, no al final: es la funcionalidad
principal del proyecto y no debe depender de que alguien llegue hasta abajo.

| | Modo construir | Modo comprar |
|---|---|---|
| Pregunta 1 | qué necesitas | qué pieza |
| Pregunta 2 | dónde queda | cuánta |
| Pregunta 3 | qué tamaño | a dónde despachamos |
| Pregunta 4 | cuándo empiezas | para cuándo |
| Formato del mensaje | encadenado con `·` | una etiqueta por renglón |

El formato lo decide cada paso con su campo `etiqueta`. Sin etiqueta las
respuestas se juntan en un renglón — compacto y suficiente cuando las opciones
se explican solas. Con etiqueta cada una ocupa su línea, que es lo que sirve
cuando Megudan va a leer el mensaje para armar un precio.

La preselección funciona por `data-intencion` en cualquier enlace de la página:
los dos botones del hero, las tarjetas de servicio y cada «Cotizar …» de los
tipos de guadua entran con la primera respuesta ya puesta.

El eje es la sección **Curado**: se fija durante 260 % de alto de pantalla y el
scroll se convierte en la línea de tiempo del material. La caña entra verde en el
corte y sale curada en el secado — el fundido entre las dos texturas se reparte a
lo largo de las cuatro etapas, no al principio. Si se resuelve antes, la sección
deja de contar algo y queda como un fondo bonito.

En celular no se fija nada: robar el scroll durante 260 vh en un pulgar se siente
como que la página se trabó. Las etapas vuelven a ser una lista que se lee.

## Texturas

En `web/src/assets/texturas/`, fotográficas y optimizadas por Astro:

| Archivo | Dónde | Papel |
|---|---|---|
| `guadua-verde.jpg` | Curado, capa inicial | la caña recién cortada |
| `guadua-curada.jpg` | Curado, capa final | la caña inmunizada y seca |
| `esterilla.jpg` | Catálogo | el material tejido que se vende |
| `follaje.jpg`, `guadual-dosel.jpg`, `guadual-verde-cerrado.jpg` | sin usar | alternativas |

Se aplican con `components/texturas/Textura.astro`, que combina `mix-blend-mode`
con una máscara de degradado. Una foto a baja opacidad sobre fondo oscuro se ve
sucia; con mezcla y máscara la textura se insinúa donde no hay texto y desaparece
donde sí.

## El cierre: el guadual que se abre bajo el pie

72 fotogramas en `web/public/secuencia/`, pintados en `<canvas>`, al final de la
portada. La página termina en el pie; quien siga bajando lo abre: el pie se
retira y el guadual desciende **del dosel al brote**, reproduciendo la secuencia
al revés. Es el movimiento contrario al del resto del sitio —que va de la
materia a la obra— y devuelve al visitante al punto de partida. Todo el tramo es
reversible: al subir, el guadual se recoge y el pie vuelve.

Solo lo monta la portada, mediante la propiedad `cierreGuadual` de `Base.astro`.
Las demás páginas llevan el pie normal.

El video de origen es de 720p y algo plano, así que el lienzo lleva
`filter: contrast/saturate/brightness` y un viñeteado. **Nada de texturas
fotográficas encima:** una imagen con estructura propia sobre el video deja
vetas fantasma.

**Los fotogramas se reparten por movimiento, no por tiempo.** El video de origen
tiene casi dos segundos muertos al principio y después acelera; extrayendo uno
cada N el visitante recorrería un cuarto de la sección para ver un 3 % del
crecimiento. `herramientas/extraer-secuencia.sh` mide la diferencia entre
fotogramas consecutivos, acumula, y elige los 72 que reparten el movimiento por
igual. Gracias a eso el mapeo en JS es lineal y no compensa nada.

Vuelve a ejecutar el script si cambia el video de origen
(`fuentes-video/guadual.mp4`, fuera de `public/` para que no acabe en el build).

**No se usa `<video>` con `currentTime`:** en iOS el seek no es fiable y el
barrido sale a tirones.

**Se descarga solo en escritorio, y solo al acercarse el pie.** Son 4,5 MB y la
mayoría de los visitantes no llega hasta abajo. En celular y con
`prefers-reduced-motion` el pie se comporta como un pie normal.

## El guadual dibujado del calificador

`components/texturas/CulmosVivos.astro`. Culmos de línea que suben desde el
suelo al entrar la sección y después se mecen apenas. Va detrás del calificador,
donde el ojo no tiene nada que hacer mientras se responde.

Dos cosas que hay que respetar si se toca:

- El SVG usa `preserveAspectRatio="none"` y todos los trazos llevan
  `vector-effect="non-scaling-stroke"`. Sin eso, estirar el viewBox a la caja
  deforma el grosor de las líneas.
- El pivote de cada culmo lo fija GSAP con **`svgOrigin`**, en coordenadas del
  viewBox. Sobre un SVG estirado, `transform-origin` de CSS —en px o en
  porcentaje, con o sin `transform-box`— no resuelve al mismo punto y los
  culmos crecen fuera de cuadro.

## El botón

`.boton-guadua` en `global.css`. Durante un tiempo el botón fue **un entrenudo**:
el tramo de caña entre dos nudos, acotado por dos bandas cerosas claras
(`--nudo-banda`, `#EDEAD8`) pegadas a los bordes. Funcionaba con la paleta
anterior, donde el relleno era un verde lima claro y la banda quedaba dentro de
la familia cálida.

Con el naranja de marca debajo dejó de funcionar: la misma banda lee como dos
cicatrices pálidas, no como el relieve de un anillo. Y `#EDEAD8` había quedado
fuera de la paleta —el claro de marca es Verde Blanco `#DBD7B9`—, así que el
token se retiró.

El nudo se queda donde sí significa algo: el marco y los divisores de sección.
Lo que ordena el botón ahora es la **jerarquía**: un solo elemento relleno por
pantalla, en el naranja de acción y con el texto en `--bg`, y lo secundario en
`.enlace-accion` —subrayado fino que se tiñe de naranja al apuntarlo—. Es también
como se comportan las piezas del manual, que no tienen botones sino titular, lema
y una sola llamada.

El naranja como losa es la única licencia que se toma el sitio frente al manual,
donde el naranja es siempre acento. Se justifica porque es el elemento que
convierte y solo hay uno por pantalla; lo que sobraba no era el color sino el
ornamento encima y un segundo botón compitiendo por la misma atención.

`.boton-guadua` se aplica a los elementos de acción rellenos o con contorno:
el primer camino de la portada, WhatsApp del menú y el flotante de móvil, las
opciones y el envío del calificador, y las llamadas del modo comprar y las
fichas de obra. Los segundos caminos de los dos hero usan `.enlace-accion`.

## El marco de guadua

`components/texturas/Marco.astro`. Las referencias de clipart resuelven «bambú»
con cañas gruesas y hojas. Aquí se destiló a lo que de verdad distingue una
estructura en guadua: **los cuatro elementos son piezas separadas que se
encuentran en la esquina, y el encuentro se resuelve con un amarre.** Eso, más
el nudo del culmo, es todo el marco. Sin hojas, sin volumen dibujado, sin verde
de caricatura — el marco va en el beige de la caña sin tratar.

Los nudos no caen a intervalos regulares: en la caña los entrenudos se acortan
hacia arriba, y las posiciones imitan esa irregularidad.

**La aparición es la del oficio, no un efecto.** Los cuatro elementos se colocan
uno tras otro girando alrededor del marco, cada uno creciendo desde la esquina
donde terminó el anterior; después se atan los amarres; y solo entonces se
descubre la foto dentro del marco ya armado.

Ningún lado se dibuja con `border`: cada uno es un elemento propio para poder
animarlo con `transform`. Un `stroke-dashoffset` daría el mismo dibujo pero
repintando en cada cuadro, y aquí hay cinco marcos con unos noventa elementos
animados entre todos.

Se aplica a los productos del modo comprar, que es donde una imagen contenida
lo admite. La portada y las bandas de obra van a sangre: enmarcarlas sería pelear
con la decisión de que la foto no tiene contenedor. El componente acepta
`proporcion`, `tinte` y `class`, así que está listo para reusarse donde haga
falta.

## Animación

`web/src/lib/motion.ts` expone tres comportamientos, activados por atributo:

- `data-revelar-texto` — el titular se descubre línea por línea tras una máscara.
- `data-revelar-palabras` — palabra por palabra; reservado al momento del curado.
- `data-entrada` — los hijos entran escalonados, con `ScrollTrigger.batch()`.
- `data-descubrir` — la imagen se descubre con `clip-path` mientras se desescala.
- `data-parallax="N"` — la foto se mueve más lento que el scroll dentro de su marco.
- `data-curado` — la secuencia fijada del curado.
- `data-marco` — el armado del marco de guadua y el descubrimiento de su foto.
- `data-avance` — la barra de lectura superior.

Todo se declara por atributo en el HTML: ningún componente importa GSAP. La
selección por medio se hace con `gsap.matchMedia()`, que además revierte solo al
cambiar de tamaño. Solo se animan `transform`, `opacity` y `clip-path`.

Todo respeta `prefers-reduced-motion`. Los titulares arrancan en
`visibility: hidden` y GSAP los revela; con movimiento reducido o sin JS quedan
visibles por CSS.

## Estructura

```
megudan/
├── assets-origen/       fotos originales de megudan.com, sin tocar (378 MB)
├── contenido/           datos extraídos + PENDIENTES.md
└── web/
    ├── src/
    │   ├── assets/      fotos optimizadas a 2400px (43 MB) — las que usa Astro
    │   ├── components/  Nav, Hero, Servicios, Portafolio, Catalogo, Pie
    │   │   └── islands/ Calificador.tsx — la única isla React
    │   ├── content/     colección proyectos
    │   ├── data/        sitio.ts, productos.json
    │   ├── layouts/     Base.astro
    │   ├── lib/         motion.ts
    │   ├── pages/       index.astro, obra/[id].astro
    │   └── styles/      tokens.css, global.css
    └── astro.config.mjs
```

## Comandos

El proyecto usa **pnpm exclusivamente** (`npm install` está bloqueado).

```bash
cd web
pnpm install
pnpm dev      # desarrollo en http://localhost:4321
pnpm build    # sitio estático en dist/
pnpm preview  # servir dist/
```

`web/pnpm-workspace.yaml` no es opcional: ancla el workspace para que pnpm no
suba hasta el `pnpm-workspace.yaml` de `$HOME`. Ver `CLAUDE.md`.

## Reprocesar imágenes

Las fotos de `assets-origen/` se reducen a 2400 px y JPEG q82 antes de entrar a
Astro. Astro luego genera los WebP responsivos en cada build.
