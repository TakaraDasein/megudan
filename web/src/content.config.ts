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

      /** Dibujo de cabecera. Uno por obra, en components/ilustraciones/obra/. */
      ilustracion: z.enum(['cercha', 'muro-tierra', 'basa', 'arco', 'capitel']),

      /**
       * La obra contada por tramos. Es la única fuente de las fotos: no hay
       * una lista plana aparte, porque tener las dos se desincroniza al primer
       * cambio. Para recorrerlas todas, `fotosDe()` en lib/obra.ts.
       *
       * El título de un tramo no siempre es una etapa constructiva. Solo tres
       * de las cinco obras tienen fotos de proceso; el Puente y el Restaurante
       * están fotografiados terminados, y ahí los tramos son momentos del
       * recorrido. Ponerles nombre de etapa sería describir fotos que no
       * existen. Mismo componente, distinto rótulo.
       */
      secciones: z
        .array(
          z.object({
            titulo: z.string(),
            /**
             * Qué se ve en las fotos del tramo. Lo consulta el muro de la
             * portada, que es un escaparate y no un diario de obra: enseña
             * primero lo construido y deja el proceso en una o dos fichas.
             * Sin esta marca tendría que deducirlo de la posición del tramo,
             * y el orden con que se cuenta una obra empieza por el barro.
             *
             * `aparte` es el tramo que no representa la obra aunque forme
             * parte de ella: el retrato del equipo, las muestras de pigmento,
             * lo que hay alrededor. Se cuenta en la ficha y no va al muro —a
             * tamaño de ficha una mano con tierra no se lee como arquitectura—.
             */
            estado: z.enum(['proceso', 'terminada', 'aparte']),
            /**
             * Solo se afirma lo que se ve en la foto: material, tipo de unión,
             * secuencia de montaje. Nada de luces, cargas, especies ni fechas
             * —eso está sin confirmar y va en contenido/PENDIENTES.md—.
             */
            texto: z.string(),
            fotos: z.array(image()).nonempty(),
          }),
        )
        .nonempty(),

      origen: z.string().url(),
    }),
});

export const collections = { proyectos };
