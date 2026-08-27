# Prompt — el guadual creciendo · secuencia para el hero

Video de 10 s que se convierte en secuencia de fotogramas. El scroll del
visitante controla el avance: la caña crece a medida que baja por la página.

## Prompt único — pégalo entero

```
Video de 10 segundos, una sola toma continua sin cortes, del crecimiento de un
guadual de guadua angustifolia en el Eje Cafetero colombiano, en time-lapse.

PLANO Y MOVIMIENTO DE CÁMARA
Plano general en contrapicado leve. La cámara arranca a un metro del suelo,
apuntando ligeramente hacia arriba a la base de un brote de guadua, y durante
los 10 segundos ejecuta UN SOLO movimiento continuo de tilt hacia arriba,
siguiendo la caña mientras crece, hasta terminar en contrapicado pronunciado
mirando el dosel contra el cielo. Sin cortes, sin saltos, sin cambios de lente,
sin travelling lateral: solo el tilt vertical, a velocidad constante.

Lente 24 mm. Profundidad de campo amplia, todo nítido de adelante atrás.
Movimiento perfectamente uniforme, sin aceleraciones ni pausas: la velocidad
debe ser lineal de principio a fin.

PROGRESIÓN DEL CRECIMIENTO, repartida pareja en los 10 segundos
Segundo 0 — Un rebrote de guadua asoma del suelo entre hojarasca: cono grueso
  cubierto de hojas caulinares pardas, de unos 30 cm. Suelo húmedo, sombra.
Segundo 2,5 — El culmo se ha elevado a unos tres metros. Verde intenso y
  ceroso, todavía envuelto en hojas caulinares que empiezan a desprenderse.
  Aparecen los primeros nudos.
Segundo 5 — Unos diez metros. Las hojas caulinares ya cayeron, el culmo está
  limpio y se ven bien los entrenudos. Otras cañas del guadual crecen alrededor
  en el mismo movimiento. Empieza a cerrarse el espacio.
Segundo 7,5 — Unos dieciocho metros. Ramas y follaje se abren en la parte alta.
  El guadual está denso; la luz llega filtrada y verde.
Segundo 10 — Guadual maduro y cerrado. Decenas de culmos verticales suben
  hacia un dosel tupido; el sol se cuela entre las hojas en haces definidos.

ATMÓSFERA Y LUZ
Luz de día constante durante toda la toma, sin ciclos de día y noche, sin
cambios de exposición ni parpadeos entre fotogramas. Ambiente húmedo de bosque
tropical andino, con neblina tenue en el fondo.

Fotografía documental de naturaleza, no render ni publicidad.
Sin personas, sin animales, sin construcciones, sin texto, sin logotipos.

COMPOSICIÓN
El cuarto inferior izquierdo del encuadre queda más oscuro y sin detalle fino:
ahí va el texto de la portada. El peso visual vive en el centro y la derecha.

FORMATO
16:9 horizontal, 4K (3840×2160), 24 fps, sin compresión agresiva.
```

## Por qué esta secuencia y no otra

La guadua alcanza sus veinte metros en seis meses. Es el dato que vuelve creíble
todo lo demás que dice el sitio sobre sostenibilidad, y no hay forma de contarlo
mejor que mostrarlo. Como el visitante controla el avance con el scroll,
el crecimiento pasa a estar en sus manos: en vez de mirar un video, lo hace
crecer.

Además encadena con lo que ya existe: el hero termina en guadual maduro, y el
Curado de `/comprar-guadua` arranca justo ahí, con la caña cortada.

## Entrega

| | |
|---|---|
| Video | 10 s · 4K · 24 fps · MP4 o MOV sin compresión agresiva |
| Fotogramas | 72 imágenes numeradas `guadual-000.webp` … `guadual-071.webp` |
| Tamaño por fotograma | 1920 px de ancho, WebP calidad 78 (~60 KB cada uno) |
| Destino | `web/public/secuencia/` |

Si entregas solo el video, yo extraigo los fotogramas.

**72 fotogramas** es el punto de equilibrio: por debajo de 60 el scrubbing se ve
a saltos, por encima de 90 el peso total deja de compensar. A 60 KB cada uno son
unos 4,3 MB, que se precargan mientras el visitante lee la portada.

**Crítico para el scrubbing:** exposición y balance de blancos bloqueados durante
toda la toma. Cualquier parpadeo de luz entre fotogramas, que en un video pasa
desapercibido, al scrubear con el scroll se ve como un temblor.

**El fotograma 0 tiene que funcionar solo**, porque es la imagen que se ve antes
de que cargue la secuencia y la que queda con `prefers-reduced-motion`.

## Cómo lo voy a montar

Los fotogramas se dibujan en un `<canvas>` y GSAP mapea el scroll al índice del
fotograma. No se usa `<video>` con `currentTime`: en iOS el seek no es fiable y
el scrubbing sale a tirones.

Con `prefers-reduced-motion` se pinta solo el fotograma 0, fijo.
