# Kiosco Sumak que gira 360° — brief de generación

Para la segunda columna de la portada: el kiosco del Restaurante Sumak, sin
fondo, que el visitante agarra con el puntero y hace girar sobre su eje.

## Antes de generar nada: lee esto

**Un modelo generativo de video no reproduce un edificio concreto con
fidelidad, y una vuelta de 360° que cierre sin costura es justo lo que peor se
le da.** Entre fotograma y fotograma la geometría deriva: cambia el número de
columnas, la cubierta se abomba, la columna central se mueve de sitio. Para un
plano de tres segundos no se nota; para una vuelta completa que el visitante
puede parar donde quiera y comparar con la foto de la obra, sí.

Hay dos caminos, y conviene saber cuál se está tomando:

| | Generativo (este documento) | Modelo 3D real |
|---|---|---|
| Fidelidad al kiosco | aproximada, «se le parece» | exacta |
| Vuelta sin costura | hay que tener suerte | garantizada |
| Fondo transparente | hay que recortar a mano | sale del render |
| Coste | minutos | un día de modelado en Blender |

Si el kiosco va a ser la cara de la portada y se va a poder inspeccionar,
**el camino bueno es el segundo**: fotogrametría a partir de las 15 fotos que
ya tenemos del Restaurante Sumak, o modelarlo en Blender siguiendo las mismas
fotos, y sacar 36 renders con alfa. Lo de abajo sirve igual para probar la idea
antes de invertir ese día, y el visor funciona idéntico con las dos fuentes.

## Resultado del primer intento (27 ago 2026)

`fuentes-video/kiosco-360.mp4` — 1280×720, 10 s, croma verde apagado
(`#60AA5B`), con una marca de agua en forma de destello abajo a la derecha.

**El kiosco salió muy bien y la vuelta no salió.** El edificio es fiel: doce
lados, teja roja, linternilla en la cumbre, baranda en aspa, columna arbórea,
dado de concreto. Pero la cámara no orbita: **oscila**. Medido fotograma a
fotograma contra el primero, la distancia sube hasta el 60, vuelve casi al
punto de partida sobre el 146 y se vuelve a ir. Es un vaivén de unas pocas
decenas de grados con un zoom encima, no una vuelta. Arrastrando, el kiosco se
mece; no se le ve la espalda.

Qué cambiar en el siguiente intento:

- Decir **«la cámara orbita 360 grados completos alrededor del edificio, una
  sola vuelta, siempre en el mismo sentido»** al principio y otra vez al final
  del prompt. Los generadores tienden a interpretar «turntable» como un
  movimiento suave de presentación.
- Prohibir explícitamente el zoom: **«la distancia de la cámara al edificio no
  cambia en ningún momento; sin acercamiento, sin alejamiento»**.
- Prohibir el vaivén: **«sin movimiento de ida y vuelta, sin oscilación»**.
- Pedir **fondo verde de croma puro `#00B140`**, no un verde apagado: el que
  vino obliga a una tolerancia estrecha para no comerse la guadua.
- Pedirlo **sin marca de agua**, o generar con la salida sin marca.

## Fotos de referencia — adjúntalas todas

Están en `web/src/assets/proyectos/restaurante-sumak/`:

| Archivo | Qué aporta |
|---|---|
| `restaurante-sumak-00b.jpg` | **La principal.** Interior completo y vacío: se lee la planta poligonal, la columna arbórea, las cerchas del perímetro y la baranda. |
| `restaurante-sumak-04.jpg` | La copa de la columna central abriéndose en abanico y el lucernario del centro. |
| `restaurante-sumak-00d.jpg` | Cómo está armada la cubierta por debajo: esterilla entre pares, cumbrera, correas. |
| `restaurante-sumak-00c.jpg` | La cubierta en dos aguas superpuestas y la altura real del espacio. |

## Cómo es la estructura, para que no la invente

Es un **kiosco poligonal de planta casi circular** —doce lados— de unos 20 m de
diámetro, todo en guadua angustifolia curada, de color miel a ámbar tostado,
con los nudos y la veta bien visibles. De fuera hacia dentro:

1. **Perímetro.** Doce columnas, cada una de dos o tres culmos atados en haz,
   arrancando de un dado de concreto bajo. Entre columna y columna, una
   **baranda de guadua en aspa** —cruces de San Andrés repetidas— a la altura
   de la cintura. El resto es aire: el kiosco no tiene muros.
2. **Anillo de cerchas.** Sobre las cabezas de las columnas corre un anillo de
   cerchitas triangulares con diagonales en zigzag entre cordón superior e
   inferior. Es la banda que se ve por debajo del alero, y da la vuelta entera.
3. **Columna arbórea, en el centro.** Un haz grueso de ocho a diez culmos
   atados que sube como un tronco y, arriba, **se abre en abanico**: cada culmo
   se separa de los demás y sale disparado en diagonal, como las palmas de una
   palmera o las varillas de un paraguas abierto, a sostener la cubierta. A
   media altura, un anillo horizontal de culmos cortos la abraza. Es la pieza
   que hay que clavar: es lo que hace reconocible al kiosco.
4. **Cubierta radial en dos niveles.** Pares de guadua salen en radio desde la
   copa de la columna hasta el anillo perimetral, formando un cono muy tendido
   de doce faldones. **La cubierta no es una sola:** hay un cono inferior
   grande y, encima y separado, un **cono superior menor —un lucernario— que
   deja una franja abierta entre los dos** por donde entra la luz. La corona un
   remate pequeño en la cumbre.
5. **Entablado.** Entre par y par, el cielo raso es de **esterilla**: guadua
   partida y aplanada, puesta en paneles rectangulares que se leen como un
   tejido de listones finos. Por encima van correas delgadas y, ya fuera,
   **teja metálica ondulada de color rojo teja**.
6. **Alero.** Vuela generoso, bastante por fuera de las columnas, y baja hasta
   quedar a poca altura del suelo: desde fuera el kiosco se lee sobre todo como
   un sombrero enorme.
7. **Piso.** Placa de concreto pulido gris, circular.

## Prompt — pégalo entero

```
Turntable de 360 grados de un kiosco de bambú guadua, aislado sobre fondo
transparente.

REGLA QUE MANDA SOBRE TODAS: es el MISMO edificio durante toda la toma. La
cámara orbita a su alrededor a velocidad constante, una sola vuelta completa,
sin cortes y sin cambiar nunca de altura ni de distancia. El edificio no se
mueve, no se deforma, no cambia de número de columnas ni de forma de cubierta
entre un instante y otro. El primer fotograma y el último tienen que ser
idénticos para que la vuelta cierre. Si la geometría cambia durante el giro, la
toma no sirve.

EL EDIFICIO
Kiosco de planta poligonal de doce lados, casi circular, de unos 20 metros de
diámetro, construido íntegramente en bambú guadua curado de color miel y ámbar
tostado, con los nudos y la veta visibles. Sin muros: es una estructura abierta.

 · Doce columnas en el perímetro, cada una de dos o tres cañas atadas en haz,
   apoyadas sobre dados bajos de concreto.
 · Entre columna y columna, una baranda de bambú en cruces de aspa a la altura
   de la cintura.
 · Sobre las columnas, un anillo continuo de cerchas triangulares con
   diagonales en zigzag entre el cordón superior y el inferior.
 · En el centro, una columna arbórea: un haz grueso de ocho a diez cañas atadas
   que sube como un tronco y arriba se abre en abanico, cada caña saliendo en
   diagonal como las varillas de un paraguas abierto, para sostener la
   cubierta. A media altura la abraza un anillo horizontal de cañas cortas.
 · Cubierta cónica muy tendida de doce faldones, con pares de bambú saliendo en
   radio desde la copa de la columna central hasta el anillo del perímetro.
 · La cubierta va en DOS niveles: un cono inferior grande y, por encima y
   separado de él, un cono superior más pequeño a modo de lucernario, con una
   franja abierta entre los dos. Un remate pequeño corona la cumbre.
 · Por fuera, la cubierta está rematada en teja metálica ondulada de color rojo
   teja. Por debajo se ve el cielo raso de bambú partido y aplanado, en paneles
   rectangulares de listones finos entre par y par.
 · El alero vuela mucho por fuera de las columnas y baja bastante: desde fuera
   el edificio se lee como un sombrero enorme sobre un anillo de columnas.
 · Piso de concreto pulido gris, circular.

CÁMARA
Órbita completa de 360 grados alrededor del eje vertical del edificio, a
velocidad constante y en un solo sentido. Cámara a unos 20 grados por encima
del edificio, en tres cuartos: lo bastante alta para leer la cubierta, lo
bastante baja para ver por debajo del alero cómo trabajan las columnas y la
columna central. Lente equivalente a 50 mm, sin distorsión de gran angular. El
edificio entero cabe en el encuadre en todo momento, con aire alrededor, y su
centro no se mueve del centro del cuadro.

LUZ
Iluminación de estudio neutra y suave, envolvente, sin sombras duras y sin
sombra proyectada en el suelo. La luz no cambia durante la vuelta.

FONDO
FONDO COMPLETAMENTE TRANSPARENTE, o en su defecto verde croma plano y uniforme
(#00B140). Sin cielo, sin terreno, sin plano de apoyo, sin horizonte, sin
niebla, sin viñeta, sin degradado. El edificio queda recortado y flotando.

NADA MÁS EN EL ENCUADRE
Sin personas, sin mesas, sin sillas, sin lámparas colgantes, sin letreros, sin
avisos, sin menús, sin vegetación, sin palmeras, sin montañas al fondo, sin
texto, sin cotas, sin logotipos, sin marca de agua.

FORMATO
Cuadrado 1:1, la mayor resolución disponible, 24 fps, 8 segundos.
```

## De video a fotogramas

El visor no consume video: consume 36 imágenes numeradas. Una vuelta de 8 s a
24 fps son 192 fotogramas; se toman 36 repartidos por igual —aquí sí por
tiempo, no por movimiento como en `extraer-secuencia.sh`, porque la órbita es
de velocidad constante y cada grado vale lo mismo.

```bash
cd megudan
mkdir -p web/public/modelo-360

# 36 fotogramas repartidos por igual a lo largo del video
ffmpeg -i fuentes-video/kiosco-360.mp4 \
  -vf "fps=36/8,scale=1200:1200:force_original_aspect_ratio=decrease" \
  -vsync 0 web/public/modelo-360/modelo-%03d.png

# Si vino en croma verde en vez de alfa, se recorta antes:
#   -vf "chromakey=0x00B140:0.14:0.06,fps=36/8,scale=1200:-1"

# A webp conservando la transparencia
cd web/public/modelo-360
for f in modelo-*.png; do
  ffmpeg -v error -i "$f" -c:v libwebp -quality 82 "${f%.png}.webp" -y
done
rm -f modelo-*.png
```

Ojo con el numerado: `ffmpeg` empieza en `001` y el visor espera desde `000`.

```bash
for i in $(seq 36 -1 1); do
  mv "modelo-$(printf %03d $i).webp" "modelo-$(printf %03d $((i-1))).webp"
done
```

## Entrega

| | |
|---|---|
| Cantidad | 36 fotogramas, uno cada 10° |
| Formato | `.webp` con canal alfa, cuadrado |
| Resolución | 1200×1200 mínimo |
| Nombres | `modelo-000.webp` … `modelo-035.webp` |
| Destino | `web/public/modelo-360/` |
| Peso | que las 36 no pasen de ~2 MB en total |

## Qué revisar antes de darlo por bueno

1. **Que la vuelta cierre.** Pon el 035 al lado del 000: si no coinciden, al
   girar habrá un salto en cada vuelta.
2. **Que el edificio no respire.** Pasa los 36 a toda velocidad. Si la cubierta
   se hincha o las columnas cambian de grosor, la toma no sirve por bonita que
   sea cada imagen suelta.
3. **Que no queden bordes verdes.** Un recorte por croma deja una orla que
   sobre el fondo oscuro del sitio se ve como un halo.
4. **Que estén las tres señas del kiosco**: la columna arbórea abierta en
   abanico, el lucernario separado de la cubierta grande, y el alero volado.
   Sin esas tres, es un kiosco cualquiera y no el de Sumak.

## Qué pasa mientras tanto

`components/Giratorio.astro` cuenta los archivos de `public/modelo-360/` en
tiempo de compilación. Si no hay ninguno —el caso de hoy— pone en su lugar la
foto interior del kiosco, y la portada se ve terminada igual. En cuanto
aparezcan los fotogramas, el giro se activa solo: no hay que tocar código.
