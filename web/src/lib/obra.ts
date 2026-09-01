import type { CollectionEntry } from 'astro:content';

/**
 * Todas las fotos de una obra, en el orden en que se cuentan.
 *
 * Las fotos viven repartidas en `secciones`, que es donde tienen sentido. Quien
 * solo necesita el montón —el muro de la portada, por ejemplo— pasa por aquí en
 * vez de obligar al .md a repetir la lista.
 */
export function fotosDe(p: CollectionEntry<'proyectos'>) {
  return p.data.secciones.flatMap((s) => s.fotos);
}

/**
 * Las fotos con las que una obra se presenta en el muro de la portada.
 *
 * El muro es un escaparate: quien pasa decide en dos segundos si esa obra se
 * parece a lo que quiere. Por eso manda lo construido, y el proceso entra solo
 * como prueba de que la obra se hizo —una o dos, no más—. Tomarlas por orden
 * de aparición, como se hacía, llenaba tres columnas de excavación.
 *
 * Cuando una obra no tiene fotos terminadas —Casa Charguayacpo sigue en
 * curso— se completa con proceso empezando por los tramos finales, que es
 * donde más se parece a un edificio. Los tramos marcados `aparte` no entran
 * nunca.
 */
export function fotosParaMuro(p: CollectionEntry<'proyectos'>, cuantas = 5, maxProceso = 2) {
  const terminadas = p.data.secciones
    .filter((s) => s.estado === 'terminada')
    .flatMap((s) => s.fotos);

  // Del final hacia atrás, y dentro de cada tramo también: la última foto del
  // último tramo es la que más se parece a un edificio en pie, que es lo único
  // que el proceso tiene que aportar aquí.
  const proceso = p.data.secciones
    .filter((s) => s.estado === 'proceso')
    .reverse()
    .flatMap((s) => [...s.fotos].reverse());

  const nProceso = Math.min(maxProceso, proceso.length, Math.max(cuantas - terminadas.length, 0) || maxProceso);
  const elegidas = [...terminadas.slice(0, cuantas - nProceso), ...proceso.slice(0, nProceso)];

  // Si aún faltan —pocas terminadas y poco proceso—, se completa con lo que quede.
  const resto = [...terminadas, ...proceso].filter((f) => !elegidas.includes(f));
  return [...elegidas, ...resto].slice(0, cuantas);
}
