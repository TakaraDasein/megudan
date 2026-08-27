// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://www.megudan.com',
  integrations: [react(), sitemap()],
  // Los tres proyectos se renombraron al nombre real que usa el cliente en las
  // fotos nuevas: Anolaima (que es el municipio de Cundinamarca donde está la
  // casa) y Sumak (el complejo de San Agustín). Las URLs viejas siguen vivas.
  redirects: {
    '/obra/estructura-en-guadua-casa-cundinamarca': '/obra/casa-anolaima',
    '/obra/plaza-de-comidas-san-agustin': '/obra/restaurante-sumak',
    '/obra/puente-san-agustin': '/obra/puente-sumak',
  },
  image: {
    // La obra se ve en pantallas grandes; conviene tener anchos generosos.
    responsiveStyles: true,
  },
});