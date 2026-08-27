# Prompt — secuencia del armado de una estructura en guadua

Para una sección nueva en la portada: «Botas y sombrero», el proceso de
levantar una obra. Es el espejo del Curado, que vive en `/comprar-guadua`.

## Prompt único — pégalo entero

```
Genera una secuencia de CUATRO imágenes fotográficas del levantamiento de una
estructura en guadua angustifolia en el Eje Cafetero colombiano.

REGLA QUE MANDA SOBRE TODAS: las cuatro imágenes comparten exactamente el mismo
encuadre, la misma posición de cámara, el mismo terreno y la misma luz. La
estructura CRECE entre una y otra; nada más cambia. Genera la imagen 1 y úsala
como referencia visual para las otras tres, añadiendo solo los elementos nuevos.
Si el punto de vista o el terreno cambian, la secuencia queda inservible.

BASE COMÚN A LAS CUATRO:
Cámara fija sobre trípode, lente de 35 mm, a la altura del pecho, ligeramente
frontal al claro. Plano general de un claro de terreno con vegetación tropical
densa al fondo. Fotografía documental de obra, no render ni publicidad.
Luz de mañana nublada, difusa y pareja, sin sombras duras ni cielos quemados.
Sin personas, sin manos, sin maquinaria, sin texto, sin logotipos.
La mitad izquierda del encuadre queda un paso más oscura y con menos detalle;
el peso visual y el detalle fino viven en la mitad derecha.
Formato 16:9 horizontal, alta resolución, color saturado y contraste marcado.

IMAGEN 1 — «Botas»
Solo la cimentación: seis pedestales de concreto y piedra que sobresalen unos
40 cm del suelo, alineados en retícula sobre el terreno limpio, cada uno con su
varilla de anclaje metálica asomando. Ninguna guadua todavía. La tierra
recién nivelada.

IMAGEN 2 — «El bosque en pie»
Sobre esos mismos pedestales, ahora seis columnas de guadua curada de color
dorado ámbar, verticales y aplomadas, de unos cuatro metros. Nada las une
todavía: solo los troncos de pie, como un guadual replantado. Los pedestales
siguen visibles bajo cada columna.

IMAGEN 3 — «La unión es el oficio»
Las mismas columnas, ahora enlazadas por vigas horizontales de guadua a dos
alturas. Los encuentros se resuelven con pernos pasantes y zunchos metálicos
visibles, y algunos amarres de fibra. Se lee claramente cómo cada pieza se
encuentra con la otra. Todavía sin cubierta.

IMAGEN 4 — «Sombrero»
La misma estructura, ahora rematada por cerchas de guadua y una cubierta de
gran alero que se proyecta bien por fuera de las columnas, protegiéndolas de la
lluvia. La estructura queda completa y a la sombra de su propio techo.
```

## Por qué estas cuatro

No es una secuencia de obra genérica. Son los dos principios que hacen que una
estructura en guadua dure —**buenas botas y buen sombrero**: la caña nunca toca
el suelo, y el alero la mantiene seca— más la unión, que es donde está el oficio.

Un visitante que va a contratar no sabe que tiene que preguntar por eso. La
sección se lo enseña y de paso explica por qué una obra bien hecha cuesta lo que
cuesta.

## Entrega

| | |
|---|---|
| Formato | 16:9 horizontal |
| Resolución | 2560×1440 mínimo |
| Archivos | PNG o JPG calidad máxima |
| Nombres | `armado-01.png` … `armado-04.png` |
| Destino | `web/src/assets/texturas/` |

**Sobre el contraste:** igual que en el Curado, la imagen se compone al 42 % con
`mix-blend-mode: soft-light` sobre fondo casi negro. Entrégala más viva y
contrastada de lo que parezca necesario, o desaparece al montarla.
