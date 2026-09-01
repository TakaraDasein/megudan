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

/* ─── Tramos de obra ─────────────────────────────────────────────────── */

const lugar: Paso = {
  id: 'lugar',
  pregunta: '¿Dónde queda?',
  opciones: ['Eje Cafetero', 'Valle del Cauca', 'Otra región'],
};

const tamano: Paso = {
  id: 'tamano',
  pregunta: '¿Qué tamaño?',
  opciones: ['Menos de 60 m²', '60 a 150 m²', 'Más de 150 m²'],
};

const momento: Paso = {
  id: 'momento',
  pregunta: '¿Cuándo empiezas?',
  opciones: ['Lo antes posible', 'En 1 a 3 meses', 'Estoy explorando'],
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
    'suministro',
  ],
};

const cantidad: Paso = {
  id: 'cantidad',
  pregunta: '¿Cuánta necesitas?',
  etiqueta: 'Cantidad',
  opciones: [
    'Menos de 50 piezas',
    'Entre 50 y 200',
    'Más de 200',
    'Necesito ayuda para calcularlo',
  ],
};

const destino: Paso = {
  id: 'destino',
  pregunta: '¿A dónde va el despacho?',
  etiqueta: 'Despacho',
  opciones: [
    'Eje Cafetero',
    'Norte del Valle',
    'Otra región del país',
    'Lo recojo yo',
  ],
};

const plazo: Paso = {
  id: 'plazo',
  pregunta: '¿Para cuándo la necesitas?',
  etiqueta: 'Plazo',
  opciones: ['Esta semana', 'En 2 a 4 semanas', 'Estoy cotizando'],
};

/* ─── Tramo de asesoría ──────────────────────────────────────────────── */

/** Las tres revisiones son las que enumera el visor en la vista `asesoria`. */
const revision: Paso = {
  id: 'revision',
  pregunta: '¿Qué hay que revisar?',
  opciones: [
    'Uniones y anclajes',
    'Inmunizado y curado',
    'Mantenimiento y reemplazo de piezas',
  ],
};

/* ─── Portada — quien va a construir ─────────────────────────────────── */

/**
 * La primera pregunta bifurca de verdad: cada opción sigue con las preguntas
 * que sirven para responderla. Antes las tres caían en el tramo de obra, así
 * que a quien venía por 200 latillas se le preguntaba el área construida y el
 * mensaje llegaba a WhatsApp sin nada con qué cotizar.
 *
 * Los tres ramales miden tres pasos a propósito: el contador dice «de 5» desde
 * el primer momento y no cambia de meta a mitad del embudo.
 */
const necesidad: Paso = {
  id: 'necesidad',
  pregunta: '¿Qué necesitas?',
  opciones: ['Diseño y construcción', 'Comprar guadua', 'Asesoría'],
  // Al enfocar cada opción, el panel de al lado muestra qué implica.
  vistas: ['construccion', 'suministro', 'asesoria'],
  ramas: [
    [lugar, tamano, momento],
    [cantidad, destino, plazo],
    [lugar, revision, momento],
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

/** Los mismos tres tramos que sigue «Comprar guadua» en la portada. */
export const suministro: Paso[] = [pieza, cantidad, destino, plazo];

/**
 * Los enlaces «Cotizar …» de cada tipo preseleccionan la pieza.
 * La clave es el `slug` del producto en `productos.json`.
 *
 * «Almas de guadua» no aparece: mientras no se confirme qué pieza es, no tiene
 * una opción propia en el calificador y su enlace cae en «Todavía no sé cuál».
 */
export const intencionesSuministro: Record<string, string> = {
  'guadua-rolliza-6-metros': 'Guadua rolliza',
  'guadua-limpia-e-inmunizada': 'Guadua limpia e inmunizada',
  'latilla-de-guauda': 'Latilla',
  'esterilla-de-guadua': 'Esterilla',
  'almas-de-guadua': 'Todavía no sé cuál',
};
