import type { Paso } from '../components/islands/Calificador';

/**
 * Dos juegos de preguntas para el mismo calificador.
 *
 * Cada pregunta existe porque cambia la respuesta que Megudan puede dar en el
 * primer mensaje. Si una pregunta no altera la cotización ni la prioridad del
 * contacto, sobra: cada paso extra pierde gente.
 *
 * Las dos ramas comparten los tramos que preguntan lo mismo —de ahí que los
 * pasos vivan sueltos y las listas se compongan más abajo—. Así la portada y
 * /comprar-guadua se dicen lo mismo con las mismas palabras sin ser la misma
 * pantalla.
 */

/**
 * Todas las vistas que un juego de preguntas puede llegar a pedir.
 *
 * El visor solo imprime estas: emitir las demás no es solo peso, es que las
 * vistas se apilan en la misma celda de la rejilla y una oculta sigue
 * ocupando alto.
 *
 * Recorre todos los pasos y no solo el primero. Antes esto era
 * `pasos[0].vistas` y el mapa de despacho —que vive en el paso 3— no se
 * emitía nunca: el panel se quedaba en el titular durante toda esa pregunta y
 * no había ningún error que lo delatara. Un arreglo `vistas` en un paso que no
 * sea el primero es perfectamente válido; lo que no existía era quien lo
 * recogiera.
 *
 * `ramas` es aparte porque la bifurcación de la portada esconde ahí media
 * embudo: sin recorrerlas, el mapa de «¿Dónde quieres construir?» —que vive dentro de la
 * rama de obra— no se emitiría nunca. Se recorren desde que la escena dejó de
 * reservar una banda fija bajo el texto y pasó a compartir celda con él: antes
 * eran 300 px de aire en reposo y los dos modos dejaban de ocupar la misma
 * caja; ahora el panel mide lo mismo con mapa que sin él.
 */
export function vistasDe(pasos: Paso[], conRamas = true): string[] {
  const vistas = pasos.flatMap((p) => [
    ...(p.vistas ?? []),
    ...(conRamas ? (p.ramas ?? []).flatMap((r) => vistasDe(r, true)) : []),
  ]);
  return [...new Set(vistas.filter((v): v is string => Boolean(v)))];
}

/* ─── Tramos de obra ─────────────────────────────────────────────────── */

/**
 * Los municipios son los del área que Megudan atiende de verdad —Pitalito y su
 * entorno, en el sur del Huila—, no regiones grandes. Nombrarlos uno por uno
 * hace dos cosas a la vez: quien es del sector se reconoce en la lista y sabe
 * que esto le queda cerca, y quien está lejos cae en «Otro municipio», que es
 * el dato que decide si hay recargo de desplazamiento.
 *
 * Si la cobertura cambia, esta lista y la de `destino` cambian juntas: son la
 * misma zona vista desde la obra y desde el despacho.
 */
const municipios = ['Pitalito', 'Bruselas', 'San Agustín', 'Isnos', 'Otro municipio'];

/* Una por municipio y en el mismo orden: son arreglos paralelos. */
const zonas = [
  'zona:pitalito',
  'zona:bruselas',
  'zona:san-agustin',
  'zona:isnos',
  'zona:otro',
];

/**
 * El sitio de la obra. La pregunta nombra lo que el visitante acaba de elegir
 * —construir— porque «¿Dónde queda?» a secas no tiene sujeto: llega justo
 * después de la bifurcación y se lee como si preguntara por algo que ya
 * existe, que es precisamente lo que aquí todavía no hay.
 */
const lugar: Paso = {
  id: 'lugar',
  pregunta: '¿Dónde quieres construir?',
  opciones: municipios,
  /* El mismo mapa que el paso de despacho, y por el mismo motivo: la pregunta
     de fondo es «¿llegan hasta donde estoy?», y se contesta enseñando la zona,
     no repitiendo el nombre del pueblo que el visitante acaba de leer en el
     botón. Es el SVG de siempre —una sola descarga para los dos embudos— y el
     mismo mecanismo `zona:`; aquí no hay nada nuevo que mantener. */
  vistas: zonas,
};

/**
 * El mismo tramo, pero en asesoría lo que se ubica es una estructura ya
 * levantada. Comparte lista y mapa con `lugar` —es la misma cobertura— y solo
 * cambia el verbo: preguntarle «¿dónde quieres construir?» a quien viene por
 * una obra suya en pie es preguntarle por otra cosa.
 */
const lugarEstructura: Paso = {
  ...lugar,
  id: 'lugar-estructura',
  pregunta: '¿Dónde está la estructura?',
};

const tamano: Paso = {
  id: 'tamano',
  pregunta: '¿Qué tamaño va a tener?',
  opciones: ['Menos de 60 m²', '60 a 150 m²', 'Más de 150 m²'],
  /* Plantas, y no alzados: la pregunta es de área y el área solo se ve desde
     arriba. Lo que crece entre las tres es la retícula de apoyos, que es lo
     que de verdad separa un tamaño de otro cuando se cotiza en guadua —no los
     metros, sino cuántas columnas hay que levantar para cubrirlos—.

     Un rango en metros cuadrados tampoco se imagina: casi nadie sabe si su
     casa tiene 80 o 140. Una planta con sus vanos sí se reconoce. */
  vistas: ['area-chica', 'area-media', 'area-grande'],
};

/**
 * Las dos preguntas de tiempo —esta y `plazo`— encienden el mismo calendario
 * del visor, cada una sobre su tramo de semanas. Doce semanas caben en el
 * dibujo, que es justo el horizonte de las dos: «1 a 3 meses» aquí y «2 a 4
 * semanas» allá.
 *
 * La tercera opción no marca nada a propósito: quien está explorando no tiene
 * fecha, y encenderle un tramo sería ponerle una que no dio.
 */
const momento: Paso = {
  id: 'momento',
  pregunta: '¿Cuándo quieres empezar la obra?',
  opciones: ['Lo antes posible', 'En 1 a 3 meses', 'Estoy explorando'],
  vistas: ['fecha:pronto', 'fecha:uno-a-tres-meses', 'fecha:abierto'],
};

/* ─── Tramos de material ─────────────────────────────────────────────── */

/**
 * Aquí las respuestas van etiquetadas, una por renglón: son datos de pedido y
 * Megudan los va a leer para armar un precio, no para hacerse una idea.
 */
const pieza: Paso = {
  id: 'pieza',
  pregunta: '¿Qué pieza necesitas?',
  etiqueta: 'Material',
  opciones: [
    'Guadua rolliza',
    'Guadua limpia e inmunizada',
    'Latilla',
    'Esterilla',
    'Almas',
    'Todavía no sé cuál',
  ],
  /* Aquí la vista no reemplaza el panel: `pieza:<slug>` enseña el recorte de
     catálogo debajo del texto, porque una presentación de material sí se
     reconoce mirándola —esa es justamente la duda que trae quien compra—. Los
     slugs son los de `productos.json`. Quien no sabe cuál necesita ve el atado
     de las cinco, que es la vista que ya existe para eso. */
  vistas: [
    'pieza:guadua-rolliza-6-metros',
    'pieza:guadua-limpia-e-inmunizada',
    'pieza:latilla-de-guauda',
    'pieza:esterilla-de-guadua',
    'pieza:almas-de-guadua',
    'suministro',
  ],
};

const cantidad: Paso = {
  id: 'cantidad',
  pregunta: '¿Cuánta guadua necesitas?',
  etiqueta: 'Cantidad',
  opciones: [
    'Menos de 50 piezas',
    'Entre 50 y 200',
    'Más de 200',
    'Necesito ayuda para calcularlo',
  ],
  /* Las tres primeras son el mismo montón a tres escalas —tres culmos, un
     atado, dos atados estibados—, así que recorrer la lista con el cursor se
     siente como ver crecer el pedido. Eso es lo que contesta la pregunta: un
     rango en piezas no se imagina, un montón sí.

     La cuarta rompe la serie porque la opción también la rompe: quien no sabe
     cuánta necesita no está eligiendo un montón más pequeño, está diciendo que
     todavía no hay montón. Ver `dibujo_calculo` en herramientas/gubia.py. */
  vistas: ['pocas', 'media', 'muchas', 'calculo'],
};

const destino: Paso = {
  id: 'destino',
  pregunta: '¿A dónde va el despacho?',
  etiqueta: 'Despacho',
  /* Los mismos municipios que `lugar` —ver su nota—, y en el mismo orden: es
     la misma zona, preguntada desde el despacho. «Lo recojo yo» se queda al
     final porque no es un lugar sino la otra manera de resolver la entrega, y
     cambia el precio tanto como el destino. */
  opciones: [...municipios, 'Lo recojo yo'],
  /* Una por opción y en el mismo orden —son arreglos paralelos—. El visor
     enciende ese municipio en el mapa del sur del Huila.

     «Otro municipio» muestra el mapa sin encender nada: la zona existe, pero
     tu punto no está en ella, y eso es exactamente lo que hay que entender
     antes de preguntar por el flete.

     «Lo recojo yo» va en `null` a propósito: no hay destino que señalar, y
     apuntar al patio sería inventarse una dirección que todavía no está
     confirmada —ver contenido/PENDIENTES.md—. */
  vistas: [...zonas, null],
};

const plazo: Paso = {
  id: 'plazo',
  pregunta: '¿Para cuándo la necesitas?',
  etiqueta: 'Plazo',
  opciones: ['Esta semana', 'En 2 a 4 semanas', 'Estoy cotizando'],
  /* El mismo calendario que `momento` —ver su nota—, sobre otras semanas. */
  vistas: ['fecha:esta-semana', 'fecha:dos-a-cuatro', 'fecha:abierto'],
};

/* ─── Tramo de asesoría ──────────────────────────────────────────────── */

/** Las tres revisiones son las que enumera el visor en la vista `asesoria`. */
const revision: Paso = {
  id: 'revision',
  pregunta: '¿Qué hay que revisar de la estructura?',
  opciones: [
    'Uniones y anclajes',
    'Inmunizado y curado',
    'Mantenimiento y reemplazo de piezas',
  ],
  /* Aquí no hay serie que crezca: las tres opciones no son más y menos de lo
     mismo sino tres asuntos distintos, así que son tres detalles —el pie que
     ancla, el tanque que cura, la pieza que sale—.

     Ninguno vuelve a dibujar una boca de pescado, y eso es deliberado: la
     lámina `union` del primer paso significa «asesoría», y si estas tres
     fueran variaciones suyas pasaría a ser una de cuatro uniones. */
  vistas: ['anclaje', 'inmunizado', 'reemplazo'],
};

/**
 * En asesoría no se empieza una obra: se agenda una visita. Mismo calendario
 * y mismos tramos que `momento` —ver su nota—, solo cambia lo que se fecha.
 */
const visita: Paso = {
  ...momento,
  id: 'visita',
  pregunta: '¿Cuándo necesitas la visita?',
};

/* ─── Portada — quien va a construir ─────────────────────────────────── */

/**
 * La primera pregunta bifurca de verdad: cada opción sigue con las preguntas
 * que sirven para responderla. Antes las tres caían en el tramo de obra, así
 * que a quien venía por 200 latillas se le preguntaba el área construida y el
 * mensaje llegaba a WhatsApp sin nada con qué cotizar.
 *
 * El ramal de compra pregunta primero la pieza —las mismas seis opciones que
 * el embudo de despacho, `pieza`—, porque sin material no hay nada que cotizar:
 * la cantidad sola no dice si son culmos, latillas o esterilla. Eso lo deja en
 * cuatro pasos frente a los tres de obra y asesoría, así que el contador pasa
 * de «de 5» a «de 6» al elegir esta opción. Se paga a sabiendas: preferimos que
 * la meta se mueva un peldaño a que el mensaje llegue a WhatsApp sin material.
 */
const necesidad: Paso = {
  id: 'necesidad',
  pregunta: '¿Qué necesitas?',
  opciones: ['Diseño y construcción', 'Comprar guadua', 'Asesoría'],
  // Al enfocar cada opción, el panel de al lado muestra qué implica.
  vistas: ['construccion', 'suministro', 'asesoria'],
  ramas: [
    [lugar, tamano, momento],
    [pieza, cantidad, destino, plazo],
    [lugarEstructura, revision, visita],
  ],
  // Primera línea del mensaje: al chat de Megudan llegan los dos embudos y
  // tiene que distinguirlos de un vistazo, igual que hacen los CTA directos.
  contextos: [
    'Quiero construir con guadua.',
    'Quiero comprar guadua.',
    'Necesito asesoría sobre una estructura que ya tengo.',
  ],
};

/** Los pasos declarados son el ramal de obra; la rama elegida sustituye la cola. */
export const construccion: Paso[] = [necesidad, lugar, tamano, momento];

/** Los botones del hero y de servicios llegan con la primera respuesta puesta. */
export const intencionesConstruccion = {
  construccion: 'Diseño y construcción',
  suministro: 'Comprar guadua',
  asesoria: 'Asesoría',
};

/* ─── /comprar-guadua — quien va a comprar material ──────────────────── */

/** Los mismos cuatro tramos que sigue «Comprar guadua» en la portada. */
export const suministro: Paso[] = [pieza, cantidad, destino, plazo];

/**
 * Los enlaces «Cotizar …» de cada tipo preseleccionan la pieza.
 * La clave es el `slug` del producto en `productos.json`, y hay una opción por
 * producto: el catálogo y el calificador ofrecen las mismas cinco piezas, así
 * que quien llega desde una ficha nunca cae en «Todavía no sé cuál».
 *
 * «Almas» va sin apellido, como «Latilla» y «Esterilla»: la lista entera habla
 * de guadua y repetirlo en cada renglón lo vuelve ruido. Lo que sigue sin
 * confirmarse de esa pieza —qué es, medidas, precio— está en
 * `contenido/PENDIENTES.md` y no hace falta para pedirla.
 */
export const intencionesSuministro: Record<string, string> = {
  'guadua-rolliza-6-metros': 'Guadua rolliza',
  'guadua-limpia-e-inmunizada': 'Guadua limpia e inmunizada',
  'latilla-de-guauda': 'Latilla',
  'esterilla-de-guadua': 'Esterilla',
  'almas-de-guadua': 'Almas',
};

/* ─── El globo del botón flotante ────────────────────────────────────── */

/**
 * EL EMBUDO DE DOS TOQUES, el que cabe en un globo al lado del botón flotante.
 *
 * No es otro calificador ni una copia recortada del de la portada: es el mismo
 * primer paso —la bifurcación, con sus mismas palabras y sus mismos contextos—
 * y UNA pregunta más, la que cada rama necesita para que el primer mensaje ya
 * traiga algo con qué contestar. Ahí se corta a propósito: pedir nombre y
 * teléfono en un globo de 300 px convierte un gesto de dos toques en un
 * formulario, y para eso ya está `#calificador`, al que el globo enlaza abajo.
 *
 * Cuál es esa segunda pregunta por rama, y por qué:
 * - construir → `lugar`. Lo que decide si Megudan puede ir y con qué recargo.
 * - comprar   → `pieza`. Sin material no hay nada que cotizar; la cantidad
 *               sola no dice si son culmos, latillas o esterilla.
 * - asesoría  → `revision`. Las tres visitas son trabajos distintos, no
 *               tamaños del mismo.
 *
 * Las dos que no traían `etiqueta` la reciben aquí: en el embudo largo esas
 * respuestas se juntan en un renglón suelto junto a las demás, pero en el
 * globo viajan solas y «Pitalito» sin rótulo no dice qué es.
 */
export const rapido = {
  primera: necesidad,
  segundas: [
    { ...lugar, etiqueta: 'Lugar' },
    pieza,
    { ...revision, etiqueta: 'Revisar' },
  ] as Paso[],
};
