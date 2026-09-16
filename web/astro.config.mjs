// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://www.megudan.com',
  integrations: [react(), sitemap()],
  /* `hover` para todo. Ya no hay dos portadas que se pidan la una a la otra
     —construir y comprar son dos modos del mismo documento—, así que lo único
     que queda por precargar son las fichas de obra, y ahí apuntar es señal
     suficiente de intención. */
  prefetch: { defaultStrategy: 'hover' },
  // Los tres proyectos se renombraron al nombre real que usa el cliente en las
  // fotos nuevas: Anolaima (que es el municipio de Cundinamarca donde está la
  // casa) y Sumak (el complejo de San Agustín). Las URLs viejas siguen vivas.
  redirects: {
    /* La rama de compra dejó de ser una página y pasó a ser un modo de la
       portada. La URL vieja sigue viva porque está repartida por fuera —en
       WhatsApp, en redes—: perderla en silencio sería romperle el enlace a
       gente que no puede avisarnos. El ancla es lo que el `<head>` lee antes de
       pintar, así que quien llegue por aquí abre directamente en el modo
       comprar y no ve un fotograma del otro. */
    '/comprar-guadua': '/#comprar',
    '/obra/estructura-en-guadua-casa-cundinamarca': '/obra/casa-anolaima',
    '/obra/plaza-de-comidas-san-agustin': '/obra/restaurante-sumak',
    '/obra/puente-san-agustin': '/obra/puente-sumak',
  },
  image: {
    // La obra se ve en pantallas grandes; conviene tener anchos generosos.
    responsiveStyles: true,
  },

  /* EL SUELO DE COMPATIBILIDAD SE DECLARA, no se hereda del empaquetador.

     Todo el movimiento del sitio viaja en scripts de módulo: `motion.ts` y la
     hidratación de las dos islas. Los `<script is:inline>` del `<head>` —el
     splash, el modo— son scripts clásicos y se ejecutan aunque los módulos no.
     Esa asimetría tiene un modo de fallo muy feo y ya medido: en un portátil
     los inline corrieron —el velo se cerró, la página se desplazaba, el hero
     se veía— y los módulos no, así que las secciones que nacen en `opacity: 0`
     esperando a GSAP no aparecieron nunca y el muro se quedó con su HTML
     servido, visible y absolutamente quieto. Sin un solo error en consola: un
     navegador que no entiende la sintaxis del módulo lo descarta en silencio.

     Sin este campo el objetivo lo elegía Vite por su cuenta y cambiaba con
     cada actualización, así que no había forma de saber contra qué se estaba
     compilando. Ahora está escrito.

     OJO: esto traduce SINTAXIS, no añade APIs. `esbuild` convertirá `?.` o
     `??` a algo que Safari 14 entienda, pero no inventa `structuredClone` ni
     `Array.at`. Si hace falta una API moderna, compruébala aquí antes.

     Van solo versiones de navegador y no una versión de ECMAScript: las dos
     cosas a la vez las rechaza el empaquetador («'es2020' is already
     specified»). Estas cuatro son el equivalente práctico de ES2020, que es
     donde entran `?.` y `??`. */
  vite: {
    build: {
      target: ['chrome87', 'edge88', 'firefox78', 'safari14'],
    },
  },
});