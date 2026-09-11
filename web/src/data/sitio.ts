/** Datos verificados del sitio anterior (megudan.com). Un solo lugar para cambiarlos. */
export const sitio = {
  nombre: 'Megudan',
  nombreLargo: 'Megudan Construcciones Sostenibles',
  /* Tagline de marca, de la línea gráfica Macro (Toolkit_Megudan.ai, lámina 10).
     Va siempre en versalitas espaciadas y en el naranja de acción, encima del
     titular, tal como la firma el manual. */
  lema: 'Lugares que respiran contigo',
  descripcion:
    'Diseñamos y construimos con guadua en el sur del Huila, y vendemos el material. Un recurso que se renueva y se corta sin acabar con la mata.',
  /* El número al que sale TODA la conversión del sitio: los dos calificadores,
     la encuesta de asesoría, el pie, el nav y los botones sueltos. Ninguno lo
     escribe por su cuenta —todos pasan por aquí o por `enlaceWhatsApp()`—, así
     que cambiarlo en esta línea lo cambia en el sitio entero.

     Formato: `whatsapp` es el internacional sin `+` ni espacios, que es lo que
     `wa.me` acepta en la ruta (57 = Colombia). `telefonoVisible` es el mismo
     número escrito para leerse. Si cambian, cambian los dos: uno marca y el
     otro se lee, y que digan cosas distintas es de los errores que nadie
     revisa hasta que un cliente llama a un número que no existe. */
  whatsapp: '573507324927',
  telefonoVisible: '350 732 4927',
  url: 'https://www.megudan.com',
} as const;

/** Abre WhatsApp con el mensaje ya escrito. Un solo punto de salida a conversión. */
export function enlaceWhatsApp(mensaje: string): string {
  return `https://wa.me/${sitio.whatsapp}?text=${encodeURIComponent(mensaje)}`;
}

export const servicios = [
  {
    id: 'construccion',
    titulo: 'Diseño y construcción',
    resumen:
      'Tu proyecto completo en guadua: vivienda, cabaña, glamping, quiosco o local. Te acompañamos desde la primera idea hasta la entrega.',
  },
  {
    id: 'suministro',
    titulo: 'Suministro de guadua',
    resumen:
      'Guadua rolliza, latilla, esterilla y almas. Material seleccionado, limpio e inmunizado, con despacho a tu obra.',
  },
  {
    id: 'asesoria',
    titulo: 'Asesoría y tratamiento',
    resumen:
      'Acompañamiento técnico, inmunizado, curado y mantenimiento de las estructuras en guadua que ya tienes.',
  },
] as const;

export type ServicioId = (typeof servicios)[number]['id'];
