# Pendientes de contenido — Megudan

> Actualizado el 2026-08-27, tras la entrega del cliente en `New/`
> (branding, catálogo de guadua y fotografía de proyectos).

Extraído automáticamente de megudan.com (Wix). Todo lo de abajo venía con texto de plantilla
o sin dato, y debe confirmarlo el cliente antes del diseño final (checklist puntos 4 y 5 de la propuesta).

## Fichas técnicas y memorias

- **Casa Charguayacpo** — memoria del proyecto (3–5 líneas)
- **Casa Charguayacpo** — ubicacion
- **Casa Charguayacpo** — anio
- **Casa Charguayacpo** — area
- **Casa 4 Gatos** — memoria del proyecto (3–5 líneas)
- **Casa 4 Gatos** — ubicacion
- **Casa 4 Gatos** — anio
- **Casa 4 Gatos** — area
- **Casa Anolaima** (antes «Estructura en guadua casa Cundinamarca») — anio
- **Casa Anolaima** — area
- **Puente Sumak** (antes «Puente San Agustín») — memoria del proyecto (3–5 líneas)
- **Puente Sumak** — anio
- **Puente Sumak** — area
- **Restaurante Sumak** (antes «Plaza de comidas San Agustin») — anio
- **Restaurante Sumak** — area
- **Esterilla de guadua** — precio real, unidad de medida y cantidad mínima (Wix mostraba $7.5, sin unidad)
- **Guadua Limpia e inmunizada.** — precio real, unidad de medida y cantidad mínima (Wix mostraba $10, sin unidad)
- **Guadua Rolliza 6 metros** — precio real, unidad de medida y cantidad mínima (Wix mostraba $20, sin unidad)
- **Almas de Guadua** — precio real, unidad de medida y cantidad mínima (Wix mostraba $20, sin unidad)
- **Latilla de guauda** — precio real, unidad de medida y cantidad mínima (Wix mostraba $25, sin unidad)

## Tipos de guadua — página /comprar-guadua

Cuatro de los cinco productos traían la descripción de plantilla de Wix
(«Soy la descripción de un producto»). Se eliminaron. Lo que hay ahora es una
definición del material —qué pieza es y para qué sirve—, que es conocimiento
general y no una afirmación sobre el inventario de Megudan.

Lo que solo puede confirmar el cliente:

- **Guadua limpia e inmunizada** — medidas y presentación
- **Latilla de guadua** — estado (verde / inmunizada / seca)
- **Latilla de guadua** — medidas y presentación
- **Esterilla de guadua** — estado (verde / inmunizada / seca)
- **Esterilla de guadua** — medidas y presentación
- **Almas de guadua** — qué pieza es y para qué se usa
- **Almas de guadua** — estado (verde / inmunizada / seca)
- **Almas de guadua** — medidas y presentación

**Almas de guadua** es el caso más urgente: no está claro qué pieza es, así que
la página la muestra con «Descripción por confirmar». Es preferible eso a
inventar una definición, pero conviene resolverlo antes de publicar.

## Resuelto con la entrega de `New/` (2026-08-27)

- **Fotografía de producto.** Los nueve recortes de `New/02. Catalogo de Guadua`
  son imágenes de producto sobre transparencia, una por presentación. Con eso se
  cierra el problema de abajo: la esterilla ya no se ilustra con la portada de
  Casa Charguayacpo. Están en `web/src/assets/productos/*-render.webp`.
  **Advertencia**: son renders, no fotografía. Se ven bien y el cliente los
  entregó como catálogo, pero conviene que él lo sepa y confirme que quiere
  vender con render en vez de con foto del material real.
- **Fotografía de obra.** Los proyectos existentes tienen portadas nuevas,
  profesionales, en lugar de las tomas de obra en bruto del sitio Wix.
- **Nombres reales de tres proyectos**, confirmados por identidad fotográfica:
  «Estructura en guadua casa Cundinamarca» y las fotos nuevas de «casa anolaima»
  son la misma casa (Anolaima queda en Cundinamarca), y el puente y la plaza de
  comidas de San Agustín son el complejo Sumak. Renombrados, con redirección
  desde las URLs viejas en `astro.config.mjs`.

## Pendiente nuevo, de la entrega de `New/`

- **Tipografía de marca.** El manual pide Condor y The Seasons. Ninguna está en
  Google Fonts y la entrega no trae licencia web. Hace falta pedir los `.woff2`
  a quien hizo el branding. Mientras tanto el sitio sigue con Archivo/Fraunces/
  Inter.
- **Fotografías de obra sin proyecto asignado.** En `New/03.proyectos` hay tres
  conjuntos con nombre genérico de exportación que no corresponden a ningún
  proyecto del sitio y que el cliente no etiquetó. Hasta saber qué son, no se
  publican:
  - **Cascarón reticulado** (`01_47_06`, `01_50_19`, `01_58_33`) — estructura de
    malla, incluida una cenital en forma de flor. Es la pieza más distintiva del
    lote.
  - **Bóvedas de esterilla** (`02_16_10`, `02_19_01`, `02_21_24`) — arcada
    abovedada.
  - **Cerramiento de latillas** (`02_31_30`, `02_33_32`) y **cubierta vista**
    (`02_33_57`, hoy asignada a Restaurante Sumak).

  Para cada una hace falta: ¿es obra de Megudan?, ¿cómo se llama el proyecto?,
  ¿dónde y de qué año?
- **Almas de guadua.** El recorte de catálogo por fin muestra la pieza, pero
  sigue sin definición escrita. No se inventó una: la ficha mantiene
  «Descripción por confirmar». Con la imagen delante debería ser rápido que el
  cliente la dicte.

## Fotografías duplicadas entre secciones

El cliente subió la misma foto a un proyecto y a un producto en Wix, así que hay
archivos byte a byte idénticos con nombres distintos. Astro los deduplica y ambos
apuntan al mismo recurso.

No rompe nada — desde que el catálogo usa `<Image>` —, pero el contenido queda
mal etiquetado: una foto de obra ilustrando un producto de catálogo.

- **Esterilla de guadua** — su primera foto es la portada de *Casa Charguayacpo*.
  Hace falta una foto de la esterilla sola, como material, no puesta en obra.

Al pedirle material al cliente conviene separar explícitamente **foto de obra** de
**foto de producto**: son dos trabajos distintos y ahora están mezclados.

## Sostenibilidad — afirmaciones por confirmar

El sitio vende con discurso de sostenibilidad, así que conviene ser exacto: ese
público detecta el greenwashing. Los textos actuales solo afirman lo que es
cierto de la guadua como especie (crece en seis meses, se corta sin matar la
mata, el guadual rebrota), nunca sobre la operación de Megudan.

Para poder decir más, hace falta que el cliente confirme:

- **Origen del material** — ¿de guaduales propios, de terceros, con plan de
  manejo aprobado por la CAR? Si hay plan de manejo, es un argumento fuerte y
  verificable que hoy no estamos usando.
- **Permiso de aprovechamiento forestal** — número y autoridad, si existe.
- **Distancia media del guadual a la obra** — respalda lo de «a unos kilómetros».
- **Qué se hace con el residuo de corte** — si se reutiliza o se composta.

Mientras no estén confirmados, no se deben añadir al sitio.

## Fichas de obra — por confirmar con el cliente

Las fichas ahora cuentan cada obra por tramos (`secciones` en el .md), y los
textos se escribieron **solo con lo que se ve en la fotografía**: material, tipo
de unión, secuencia de montaje. Falta que el cliente confirme lo que ninguna
foto puede decir, y que hoy no está en el sitio:

- **Casa 4 Gatos** — el `sistema` decía «Guadua angustifolia» y las 17 fotos de
  proceso son tapia pisada, ladrillo y concreto sobre sobrecimiento de piedra;
  la guadua aparece solo en el kiosco. Quedó como «Tapia pisada y guadua
  angustifolia». **Confirmar con el cliente cómo quiere nombrar ese sistema**, y
  si la casa y el kiosco son un solo encargo o dos.
- **Puente Sumak y Restaurante Sumak** — no hay una sola foto de proceso. Sus
  tramos son momentos del recorrido, no etapas de obra. Si el cliente conserva
  fotos del montaje, esas dos fichas mejoran más que ninguna otra: son las dos
  obras más vistosas y las únicas que no pueden mostrar cómo se hicieron.
- **Luces, cargas y dimensiones** — nada de esto se afirma en los textos porque
  no es verificable en foto. Confirmar al menos la luz del Puente Sumak y el
  diámetro del comedor del Restaurante: son los dos datos que un cliente
  técnico va a buscar.
- **Casa Charguayacpo** — está sin terminar y solo hay 7 fotos. Preguntar si la
  obra sigue en curso, para saber si conviene pedir material nuevo o dejarla
  fuera del portafolio.
