#!/usr/bin/env node
/**
 * La imagen que acompaña al enlace cuando alguien lo comparte.
 *
 * QUÉ RESUELVE. El sitio no declaraba `og:image`, así que al pegar el enlace en
 * WhatsApp —que es a donde lleva cada pantalla de este sitio— salía una tarjeta
 * sin imagen: título, descripción y un hueco gris. El enlace más importante del
 * negocio era el que peor se veía.
 *
 * POR QUÉ UN PNG Y NO EL SVG QUE YA ESTÁ EN `public/marca/`. Los raspadores de
 * enlaces no son navegadores: **WhatsApp no dibuja SVG ni WebP** en la vista
 * previa. Si `og:image` apunta a uno, la tarjeta sale sin imagen y no hay
 * ningún aviso —lo mismo que pasaría con una ruta relativa, que también hay que
 * dar absoluta—. Por eso esto existe: para rasterizar el mismo logo a un
 * formato que el raspador sí entienda.
 *
 * NO SE EDITA A MANO: se regenera con `node herramientas/og-imagen.mjs` cuando
 * cambie el logo o el color de fondo.
 *
 * EL LOGO VA ESTRECHO A PROPÓSITO. La lona es 1200x630 —la proporción que hace
 * que WhatsApp enseñe la tarjeta grande en vez de una miniatura al margen—,
 * pero según dónde se pegue el enlace la previa se recorta a un CUADRADO
 * CENTRADO. Con el logo a 560 px cabe entero dentro de ese recorte de 630, así
 * que la marca sobrevive a las dos formas. Ensancharlo hasta llenar la lona se
 * ve mejor en la tarjeta ancha y pierde las puntas en la cuadrada.
 *
 * El logo ya viene en `#DBD7B9` —el mismo Verde Blanco del texto del sitio—
 * sobre el Negro Verde del fondo, así que no hay que recolorearlo: la tarjeta
 * usa la paleta de marca sin inventarse nada.
 */
import { createRequire } from 'node:module';
import { mkdir, writeFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

/* `sharp` vive en `web/node_modules` y este script no. Se resuelve desde el
   `package.json` de `web/` en vez de por el árbol de carpetas, que desde
   `herramientas/` no llega. */
const require = createRequire(new URL('../web/package.json', import.meta.url));
const sharp = require('sharp');

const RAIZ = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const LOGO = path.join(RAIZ, 'web', 'public', 'marca', 'logo.svg');
const DESTINO = path.join(RAIZ, 'web', 'public', 'og', 'megudan.png');

const ANCHO = 1200;
const ALTO = 630;
const FONDO = { r: 0x1d, g: 0x23, b: 0x16, alpha: 1 }; // --bg, Negro Verde
const ANCHO_LOGO = 560;

const logo = await sharp(LOGO, { density: 400 })
  .resize({ width: ANCHO_LOGO })
  .png()
  .toBuffer();
const { height: altoLogo } = await sharp(logo).metadata();

const lona = sharp({
  create: { width: ANCHO, height: ALTO, channels: 4, background: FONDO },
});

await mkdir(path.dirname(DESTINO), { recursive: true });
const salida = await lona
  .composite([
    {
      input: logo,
      left: Math.round((ANCHO - ANCHO_LOGO) / 2),
      top: Math.round((ALTO - altoLogo) / 2),
    },
  ])
  // `palette` porque esto son dos colores planos: baja de unos 40 KB a menos de
  // diez sin que se note. WhatsApp deja de enseñar la imagen si pesa mucho, y
  // cuanto más lejos del límite, menos hay que pensar en ello.
  .png({ palette: true, compressionLevel: 9 })
  .toBuffer();

await writeFile(DESTINO, salida);
const { size } = await stat(DESTINO);
console.log(
  `· ${path.relative(RAIZ, DESTINO)}  ${ANCHO}x${ALTO}  ` +
    `logo ${ANCHO_LOGO}x${altoLogo}  ${(size / 1024).toFixed(1)} KB`,
);
