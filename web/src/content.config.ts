import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const proyectos = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/proyectos' }),
  schema: ({ image }) =>
    z.object({
      titulo: z.string(),
      tipo: z.enum(['Vivienda', 'Estructura', 'Infraestructura', 'Comercial']),
      // Los nulos son datos que el cliente aún no ha confirmado (ver contenido/PENDIENTES.md).
      ubicacion: z.string().nullable(),
      anio: z.number().nullable(),
      area: z.number().nullable(),
      sistema: z.string(),
      orden: z.number(),
      portada: image(),
      galeria: z.array(image()),
      origen: z.string().url(),
    }),
});

export const collections = { proyectos };
