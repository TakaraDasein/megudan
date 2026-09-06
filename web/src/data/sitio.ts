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
  whatsapp: '573027501200',
  telefonoVisible: '302 750 1200',
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
