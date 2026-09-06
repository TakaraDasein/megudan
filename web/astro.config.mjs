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
});