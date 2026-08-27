# Prompt — secuencia del curado de la guadua

Para el fondo de la sección «Una caña no sirve hasta que se cura» (4 etapas).

## La regla que manda sobre todas

**La composición no cambia entre las cuatro etapas.** Las mismas cañas, en las
mismas posiciones, con el mismo encuadre y la misma luz. Lo único que cambia es
el estado del material.

Si cada etapa trae un montón distinto de guadua, el fundido se ve como un pase
de diapositivas. Si son las mismas cañas cambiando, se ve como el material
transformándose — que es lo que la sección cuenta.

En la práctica: genera la etapa 1 y usa esa imagen como referencia para las
otras tres, pidiendo solo el cambio de estado.

---

## Prompt base (común a las cuatro)

```
Primer plano de una pared de culmos de guadua angustifolia verticales que llenan
todo el encuadre, vistos de frente y muy de cerca. Ocho a diez cañas de entre 10
y 12 cm de diámetro, juntas, con sus nudos visibles a distintas alturas. Fondo
completamente ocupado por las cañas, sin cielo ni horizonte.

Cámara fija, sin paneo ni zoom. Lente de 50 mm a la altura del pecho,
perpendicular a las cañas. Profundidad de campo amplia: la fibra se lee nítida
en toda la superficie.

Fotografía documental de material, no publicidad. Sin personas, sin manos, sin
herramientas, sin texto, sin logotipos, sin marcas de agua.

Iluminación pareja y suave, sin reflejos quemados. La mitad izquierda del
encuadre queda un paso más oscura y con menos detalle; el detalle fino de la
fibra y los nudos vive en la mitad derecha.

Formato 16:9 horizontal, alta resolución.
```

---

## Las cuatro etapas — solo cambia este bloque

### 01 · Corte en menguante
```
Estado: caña recién cortada, viva. Verde intenso y saturado, con la cerosidad
blanquecina propia del culmo joven en los entrenudos. Superficie tersa y turgente.
Luz de madrugada, fría y azulada, antes del amanecer.
```

### 02 · Avinagrado en pie
```
Estado: la misma caña varios días después, apoyada y transpirando. El verde
empieza a apagarse y a virar hacia el oliva; aparecen vetas amarillentas en los
bordes de cada culmo y cerca de los nudos. La cerosidad se ha ido.
Luz de día nublado, difusa y neutra.
```

### 03 · Inmunizado
```
Estado: la misma caña recién salida de la inmersión en sales de boro. Superficie
mojada y brillante, con gotas y escurrimientos. El color se oscurece a un oliva
pardo profundo y húmedo, y el brillo del agua marca la curva de cada culmo.
Luz lateral suave que revela el reflejo húmedo.
```

### 04 · Secado bajo cubierta
```
Estado: la misma caña ya seca y curada. Color dorado cálido, ámbar apagado, con
las vetas longitudinales de la fibra bien visibles y los nudos más oscuros que
el resto. Acabado mate, nada de brillo. Alguna fisura fina de secado.
Luz de sombra bajo cubierta, cálida y tenue.
```

---

## Especificaciones de entrega

| | |
|---|---|
| Formato | 16:9 horizontal |
| Resolución | 2560×1440 mínimo (mejor 3840×2160) |
| Archivos | PNG o JPG calidad máxima — **nada de capturas de video comprimido** |
| Cantidad | 4 imágenes, una por etapa |
| Nombres | `curado-01.png` … `curado-04.png` |

**Importante sobre el contraste.** La imagen se monta al 42 % de opacidad con
`mix-blend-mode: soft-light` sobre un fondo casi negro (`#141711`). Ese modo
aplasta mucho el rango, así que el material tiene que llegar **saturado y con
contraste marcado**. Una imagen ya oscura o desvaída desaparece por completo al
componerla. Si dudas, entrégala más viva de lo que parece necesario.

**Si de todos modos lo haces en video** (Veo o similar): 10–12 segundos, cámara
totalmente fija, transiciones por disolvencia entre los cuatro estados, sin corte
duro, 4K, sin compresión agresiva. De ahí saco los cuatro fotogramas.

---

## Dónde van

En `web/src/assets/texturas/`. Hoy la sección cruza dos capas
(`guadua-verde.jpg` → `guadua-curada.jpg`) repartidas a lo largo de las cuatro
etapas. Con cuatro imágenes cada etapa tendrá su propio estado y el cambio de
material quedará sincronizado paso a paso con el texto.
