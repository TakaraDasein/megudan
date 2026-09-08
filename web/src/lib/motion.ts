import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { SplitText } from 'gsap/SplitText';

gsap.registerPlugin(ScrollTrigger, SplitText);

/**
 * Todo el movimiento del sitio se declara por atributo en el HTML y se conecta
 * aquí. Ningún componente importa GSAP por su cuenta.
 *
 * Regla de rendimiento: solo se animan `transform`, `opacity` y `clip-path`.
 * Nada que provoque recálculo de layout.
 */

/* ------------------------------------------------------------------ *
 * Revelado de texto
 * ------------------------------------------------------------------ */

/**
 * `data-revelar-texto` — el titular se descubre línea por línea tras una
 * máscara, como una cercha que se arma de abajo hacia arriba.
 *
 * Se usa máscara en vez de fundido porque el texto nunca aparece translúcido:
 * o está o no está, igual que una pieza puesta en obra.
 */
function revelarTexto(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-revelar-texto]').forEach((el) => {
    // Los titulares de la obertura los mueve ella, en su turno de la fila.
    if (el.closest('[data-obertura]')) return;
    const split = SplitText.create(el, { type: 'lines', mask: 'lines' });
    el.style.visibility = 'visible';

    gsap.from(split.lines, {
      yPercent: 115,
      duration: 1,
      ease: 'power4.out',
      stagger: 0.08,
      scrollTrigger: { trigger: el, start: 'top 88%', once: true },
    });
  });
}

/**
 * `data-revelar-palabras` — reservado para el momento narrativo del curado.
 * Las palabras entran de una en una, con el peso de una lista de materiales.
 */
function revelarPalabras(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-revelar-palabras]').forEach((el) => {
    const split = SplitText.create(el, { type: 'words', mask: 'words' });
    el.style.visibility = 'visible';

    gsap.from(split.words, {
      yPercent: 110,
      opacity: 0,
      duration: 0.7,
      ease: 'power3.out',
      stagger: 0.045,
      scrollTrigger: { trigger: el, start: 'top 85%', once: true },
    });
  });
}

/**
 * `data-voltear` — el titular se arma letra por letra, cada una girando sobre
 * su propio eje horizontal hasta quedar de frente.
 *
 * Es el gesto de la guadua puesta en obra: la pieza llega tumbada y se levanta
 * a su sitio. Por eso gira desde abajo (`rotationX` negativo) y con el eje de
 * giro empujado hacia atrás —`transformOrigin` con una Z negativa—: la letra
 * bascula como una tabla con bisagra al fondo, no como un naipe que gira sobre
 * su propio plano.
 *
 * Diferencias deliberadas con el componente del que sale la idea:
 *
 *  1. No es una isla. El volteo no depende del puntero ni de un bucle de
 *     fotogramas, así que no justifica una tercera isla React: se declara por
 *     atributo, como todo el movimiento del sitio.
 *  2. No se repite. El original gira en bucle infinito; encima del muro de
 *     obra —veinticinco fotografías ya en movimiento— un titular que no para
 *     de voltear le compite al muro en vez de abrirlo. Una pasada, `once`.
 *  3. Se parte por letras pero se agrupa por palabras (`type: 'words,chars'`),
 *     así el nombre de la obra no se corta a media palabra al encoger la
 *     ventana.
 *
 * La perspectiva va por letra (`transformPerspective`) y no en el contenedor:
 * con una sola perspectiva compartida, las letras de los extremos se ven desde
 * muy de lado y se deforman en trapecio; por letra, cada una se ve de frente.
 */
function voltearTexto(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-voltear]').forEach((el) => {
    const split = SplitText.create(el, { type: 'words,chars' });
    el.style.visibility = 'visible';

    gsap.set(split.chars, {
      display: 'inline-block',
      transformPerspective: 900,
      // La Z negativa mete la bisagra por detrás del papel: el giro describe un
      // arco corto hacia el visitante en vez de quedarse plano.
      transformOrigin: '50% 60% -0.4em',
    });

    gsap.from(split.chars, {
      rotationX: -104,
      yPercent: 26,
      opacity: 0,
      // Corta y con rebote: `back.out` pasa un poco de la vertical y vuelve,
      // que es el golpe seco de la pieza al asentar. Con `power3.out` y 0,9 s
      // cada letra frenaba durante medio segundo sin llegar a nada, y lo que
      // se veía era el frenado, no el giro.
      duration: 0.52,
      ease: 'back.out(1.7)',
      stagger: retrasoPorLetra,
      scrollTrigger: { trigger: el, start: 'top 88%', once: true },
    });
  });
}

/**
 * Retraso de cada letra dentro del volteo, en segundos.
 *
 * GSAP llama a esta función una vez por letra y usa lo que devuelve como su
 * retraso propio: el reparto del escalonado se decide aquí y en ningún otro
 * sitio.
 *
 * @param i     índice de la letra, de 0 a `total - 1`.
 * @param letra el elemento de esa letra.
 * @param todas todas las letras del titular.
 * @returns     segundos de espera antes de que esa letra empiece a girar.
 */
function retrasoPorLetra(i: number, letra: Element, todas: Element[]): number {
  const total = Math.max(todas.length - 1, 1);
  const t = i / total;
  // Seno, como el componente del que sale la idea, pero INVERTIDO: allí el
  // reparto se abre al principio y se aprieta al final —las primeras letras
  // separadísimas y el cierre en montón—, y con veintiuna letras eso se lee
  // como una máquina de escribir que se atasca al final.
  //
  // Aquí arranca apretado y se abre: las primeras letras salen casi juntas
  // —el titular aparece de golpe, que es lo vistoso— y la cola se despliega en
  // abanico, que es lo que deja ver el giro. Es la misma curva que usa el
  // revelado por líneas, y no por casualidad.
  const curva = 1 - Math.cos(t * (Math.PI / 2));

  // 0,26 s de reparto y 0,52 s de tween: el titular entero se arma en 0,78 s,
  // por debajo del segundo que separa una entrada de una espera. El techo
  // importa más que el paso: con un retraso fijo por letra, un titular largo
  // se alarga sin límite, y este cambia de longitud según el modo.
  return curva * 0.26;
}

/* ------------------------------------------------------------------ *
 * Entradas
 * ------------------------------------------------------------------ */

/**
 * `data-entrada` — los hijos directos entran escalonados.
 * Usa `batch` para no crear un ScrollTrigger por elemento.
 */
function entradas(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-entrada]').forEach((cont) => {
    if (cont.closest('[data-obertura]')) return;
    const hijos = Array.from(cont.children) as HTMLElement[];
    gsap.set(hijos, { opacity: 0, y: 28 });

    ScrollTrigger.batch(hijos, {
      start: 'top 88%',
      once: true,
      onEnter: (lote) =>
        gsap.to(lote, {
          opacity: 1,
          y: 0,
          duration: 0.75,
          ease: 'power2.out',
          stagger: 0.09,
          overwrite: true,
        }),
    });
  });
}

/**
 * La obertura, ya puesta y sin gesto.
 *
 * Es lo que corre cuando se llega a una portada navegando —cruzar entre las dos
 * ramas, o volver con el botón de atrás—, y no en la carga en frío. La entrada
 * escalonada es la continuación del splash: sin splash delante no continúa
 * nada, y encima estorba. Al cruzar de rama la transición del navegador dura
 * 320 ms y la obertura casi 1.3 s, así que la portada de destino llegaba en
 * tres tiempos —un hueco oscuro donde el contenido viejo ya se fue y el nuevo
 * aún está en `opacity: 0`, luego la fotografía de golpe y sola, y por último
 * el texto goteando encima—. Ese salto del hueco oscuro a la foto a plena luz
 * es lo que se ve como un parpadeo.
 *
 * El estado inicial de `[data-alza]` vive en el CSS (`html[data-js]`), así que
 * hay que devolverlo a la vista con estilo en línea; y los titulares con
 * máscara van escondidos por `visibility`, que `revelarTexto` no les levanta
 * porque se salta todo lo que cuelga de `[data-obertura]`.
 */
function oberturaYaPuesta(root: ParentNode) {
  // Sin velo no hay nada escondido que devolver a la vista, así que no se toca
  // el DOM: el estado inicial de la obertura cuelga de
  // `html[data-splash='abierto']` (ver global.css) y ese atributo solo existe
  // en la carga en frío. Navegando por el router esta función escribía en línea
  // los valores que ya eran los efectivos —pagaba el precio sin comprar nada—,
  // y el precio era caro: los `[data-alza]` de la portada son los mismos
  // elementos que llevan `transition:name`, y escribirles una transformada
  // mientras el navegador los tiene capturados desancla sus instantáneas.
  if (document.documentElement.dataset.splash !== 'abierto') return;

  root.querySelectorAll<HTMLElement>('[data-obertura]').forEach((cont) => {
    cont
      .querySelectorAll<HTMLElement>('[data-revelar-texto], [data-revelar-palabras]')
      .forEach((el) => (el.style.visibility = 'visible'));
    // `clearProps` y no `y: 0, scale: 1`: devuelve el elemento a su estilo de
    // hoja en vez de dejarle una transformada en línea que no hacía falta.
    gsap.set(cont.querySelectorAll('[data-alza]'), { opacity: 1, clearProps: 'transform' });
  });
}

/**
 * `data-obertura` / `data-alza` — la entrada de la portada.
 *
 * Lo que hay sobre el pliegue no puede depender del scroll: ya está a la vista
 * cuando la página abre, así que un ScrollTrigger dispararía todo a la vez y
 * —peor— lo haría por detrás del splash, que dura más. Aquí la fila se ordena
 * a mano: los `[data-alza]` suben en el orden en que están escritos, de abajo
 * hacia arriba, uno detrás de otro.
 *
 * El ritmo es el del splash y no otro: el escalonado (85 ms) es el mismo
 * intervalo con el que el relleno del logo recorre su altura, y cada pieza
 * llega con un resto de escala —0.985 → 1— que repite, en pequeño, el gesto
 * con el que el logo se va hacia el visitante. La página no arranca después
 * del splash: lo continúa.
 *
 * Quien la dispara es `iniciarMovimiento`, y eso ocurre cuando el velo empieza
 * a abrirse (ver Base.astro y Splash.astro). Solo en la carga en frío: llegando
 * por el router no hay splash que continuar y corre `oberturaYaPuesta`.
 */
function obertura(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-obertura]').forEach((cont) => {
    const pasos = Array.from(cont.querySelectorAll<HTMLElement>('[data-alza]'));
    if (!pasos.length) return;

    // El estado escondido pasa del CSS al estilo en línea antes de armar nada.
    // La regla de global.css cuelga de `[data-splash='abierto']`, y el splash
    // borra ese atributo a mitad de la obertura: sin fijarlo aquí, los pasos
    // que aún no han empezado su turno se harían visibles de golpe en cuanto el
    // velo termina.
    gsap.set(pasos, { opacity: 0 });

    const linea = gsap.timeline({ defaults: { ease: 'power3.out' } });

    pasos.forEach((el, i) => {
      const t = i * 0.085;

      // Un titular no entra como bloque: entra por líneas, tras su máscara,
      // igual que en el resto del sitio. Solo cambia quién le da la salida.
      if (el.hasAttribute('data-revelar-texto')) {
        const split = SplitText.create(el, { type: 'lines', mask: 'lines' });
        el.style.visibility = 'visible';
        linea
          .set(el, { opacity: 1 }, t)
          .from(split.lines, { yPercent: 115, duration: 0.95, stagger: 0.07 }, t);
        return;
      }

      linea.fromTo(
        el,
        { opacity: 0, y: 30, scale: 0.985 },
        { opacity: 1, y: 0, scale: 1, duration: 0.85, clearProps: 'transform' },
        t,
      );
    });
  });
}

/**
 * `.nudo` — la junta entre secciones se traza al llegar a ella.
 *
 * Cada sección abre en un nudo, y el nudo son dos trazos: la regla —el filete
 * de 1 px a todo el ancho— y la marca —el acento corto en verde oliva, alineado
 * al margen del texto—. Se dibujan de izquierda a derecha, la regla primero y
 * la marca un pelo detrás: es el orden en que se arma una cercha, primero el
 * tirante y luego el nudo que lo amarra.
 *
 * Antes la junta era un elemento quieto: todo el movimiento estaba en el
 * contenido (`data-entrada`, `data-revelar-texto`) y el paso de una sección a
 * otra no lo acompañaba nadie. Se cruzaba una línea inerte, y eso es lo que
 * hacía que la página se leyera plana por mucho que cada bloque entrara bien.
 *
 * Arranca en `top 92%`, antes que las entradas de contenido (`top 88%`): la
 * junta se traza y el contenido llega detrás, no al revés.
 *
 * Se anima una variable y no la transformada directamente porque quien lleva
 * los trazos son `::before` y `::after`, y a un pseudoelemento no se le puede
 * apuntar desde JavaScript. Las dos variables están registradas con `@property`
 * en global.css para que el navegador las interpole como números.
 */
function juntas(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('.nudo').forEach((junta) => {
    gsap
      .timeline({
        defaults: { ease: 'power3.out' },
        scrollTrigger: { trigger: junta, start: 'top 92%', once: true },
      })
      .to(junta, { '--nudo-regla': 1, duration: 0.9 })
      .to(junta, { '--nudo-marca': 1, duration: 0.45, ease: 'power2.out' }, 0.16);
  });
}

/**
 * `data-morfo` — congela la banda de verbos mientras no se la ve.
 *
 * El fundido de la banda lleva un filtro SVG y un desenfoque animado: mientras
 * corre, el navegador repinta esa caja en cada fotograma, esté o no en pantalla.
 * Aquí solo se conmuta una variable —el CSS la lee en `animation-play-state`—,
 * así que sin JavaScript la banda sigue animándose igual.
 */
/**
 * Lo que hay que SOLTAR a mano al desmontar: escuchas globales y bucles del
 * ticker.
 *
 * `gsap.Context` —y con él `matchMedia().revert()`— recoge los tweens y los
 * ScrollTrigger que se crean dentro, pero NO un `gsap.ticker.add` ni un
 * `window.addEventListener`. Esos sobreviven al desmontaje.
 *
 * Importa desde que la portada tiene dos modos: cambiar de modo es un rearme
 * completo, así que sin esto cada cruce dejaba vivo el bucle anterior del
 * modelo giratorio, dibujando sobre un `<canvas>` que ya no está en el
 * documento, y encima apilaba uno nuevo. Medido: 73 escuchas de `resize`
 * acumuladas tras tres cruces, y un bucle por cada visita a la portada.
 *
 * Con esto, el modelo queda pausado mientras se está en el modo comprar
 * —porque su bucle se soltó— y vuelve a armarse al regresar a construir. No
 * hace falta una bandera de pausa: hace falta limpiar.
 */
type Soltar = (fn: () => void) => void;

function morfo(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-morfo]').forEach((banda) => {
    const estado = (v: string) => banda.style.setProperty('--morfo-estado', v);
    const st = ScrollTrigger.create({
      trigger: banda,
      start: 'top bottom',
      end: 'bottom top',
      onToggle: (self) => estado(self.isActive ? 'running' : 'paused'),
    });
    // El estado inicial se decide aquí y no antes de crear el disparador:
    // `onToggle` solo avisa de los cambios, y dejarla en pausa «por defecto»
    // significaría que una banda ya visible al cargar se queda en su fotograma
    // cero, que es opacidad cero.
    estado(st.isActive ? 'running' : 'paused');
  });
}

/**
 * `data-descubrir` — la imagen se descubre desde abajo con una máscara que
 * sube, mientras la foto misma baja un poco. Da la sensación de que la pieza
 * se coloca en su sitio, no de que aparece.
 */
function descubrirImagenes(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-descubrir]').forEach((marco) => {
    const img = marco.querySelector('img');
    if (!img) return;

    gsap
      .timeline({ scrollTrigger: { trigger: marco, start: 'top 85%', once: true } })
      .fromTo(
        marco,
        { clipPath: 'inset(100% 0 0 0)' },
        { clipPath: 'inset(0% 0 0 0)', duration: 1.15, ease: 'power3.inOut' },
      )
      .from(img, { scale: 1.14, duration: 1.4, ease: 'power3.out' }, 0);
  });
}

/**
 * Índice de fotograma con vaivén opcional.
 *
 * Una secuencia de 360° cierra sola: el último fotograma empalma con el
 * primero y basta el módulo. Un barrido que no da la vuelta, no: al saltar del
 * último al primero se ve un corte. El vaivén recorre la secuencia de ida y de
 * vuelta —periodo `2n-2`, sin repetir los extremos—, así que el bucle es
 * continuo y no cuesta un solo archivo de más.
 */
function fotograma(i: number, total: number, vaiven: boolean) {
  if (!vaiven) return ((Math.round(i) % total) + total) % total;
  const periodo = Math.max(1, 2 * total - 2);
  const x = ((Math.round(i) % periodo) + periodo) % periodo;
  return x < total ? x : periodo - x;
}

/**
 * `data-indice` — el visor fijo del índice de obra sigue a la lectura.
 *
 * Cada fila enciende su lámina cuando cruza la mitad de la pantalla, y también
 * al pasar el cursor por encima: en escritorio la mano suele ir por delante de
 * la lectura, y esperar al scroll se sentiría lento.
 *
 * No hay `pin` ni scrub. La lámina es `position: sticky` y esto solo decide
 * cuál se ve: el desplazamiento sigue siendo del visitante.
 */
function indiceObra(ctx: gsap.Context, root: ParentNode, conMovimiento: boolean) {
  root.querySelectorAll<HTMLElement>('[data-indice]').forEach((caja) => {
    const filas = Array.from(caja.querySelectorAll<HTMLElement>('[data-fila]'));
    const laminas = Array.from(caja.querySelectorAll<HTMLElement>('[data-lamina]'));
    if (!filas.length || !laminas.length) return;

    let activa = -1;
    const encender = (i: number) => {
      if (i === activa || i < 0) return;
      activa = i;
      filas.forEach((f, k) => f.classList.toggle('activa', k === i));
      laminas.forEach((l, k) => l.classList.toggle('activa', k === i));
    };
    encender(0);

    filas.forEach((fila, i) => {
      fila.addEventListener('mouseenter', () => encender(i));
      fila.addEventListener('focus', () => encender(i));

      if (!conMovimiento) return;
      ScrollTrigger.create({
        trigger: fila,
        start: 'top 55%',
        end: 'bottom 55%',
        onToggle: ({ isActive }) => isActive && encender(i),
      });
    });
  });
}

/**
 * `data-rotante` — el remate del titular cambia de frase cada pocos segundos.
 *
 * Las frases ya están todas en el HTML, apiladas en la misma celda de rejilla:
 * la caja mide de entrada lo que la más alta, así que al girar no se mueve
 * nada de lo que hay debajo. Aquí solo se enciende una y se apagan las demás.
 *
 * El relevo entra desde abajo y sale por arriba —la frase nueva empuja a la
 * vieja, no la sustituye—, que es el mismo gesto que el revelado del titular.
 * El solape de 0,2 s evita el parpadeo de un instante con la caja vacía.
 *
 * Accesibilidad: solo la frase visible queda expuesta. Sin marcar las otras,
 * un lector de pantalla leería el titular con las tres promesas seguidas.
 */
function rotante(ctx: gsap.Context, root: ParentNode, conMovimiento: boolean) {
  root.querySelectorAll<HTMLElement>('[data-rotante]').forEach((caja) => {
    const frases = Array.from(caja.querySelectorAll<HTMLElement>('.frase'));
    if (frases.length < 2) return;

    const exponer = (i: number) =>
      frases.forEach((f, k) => f.setAttribute('aria-hidden', String(k !== i)));

    gsap.set(frases, { opacity: 0, yPercent: 30 });
    gsap.set(frases[0], { opacity: 1, yPercent: 0 });
    exponer(0);

    // Con movimiento reducido no rota: se queda la primera. Tres frases que se
    // turnan solas son justo lo que esa preferencia pide evitar.
    if (!conMovimiento) return;

    /** Lo que se queda quieta cada frase, en segundos. */
    const LECTURA = 3.6;
    let i = 0;

    const girar = () => {
      const sale = frases[i];
      i = (i + 1) % frases.length;
      const entra = frases[i];
      // La entrante se expone ya; la saliente no se oculta hasta que termina de
      // irse. Marcarla antes deja medio segundo en que se ve una frase que el
      // lector de pantalla da por ausente.
      entra.setAttribute('aria-hidden', 'false');

      gsap
        .timeline({ onComplete: () => gsap.delayedCall(LECTURA, girar) })
        .to(sale, {
          yPercent: -30,
          opacity: 0,
          duration: 0.45,
          ease: 'power2.in',
          onComplete: () => sale.setAttribute('aria-hidden', 'true'),
        })
        .fromTo(
          entra,
          { yPercent: 30, opacity: 0 },
          { yPercent: 0, opacity: 1, duration: 0.65, ease: 'power3.out' },
          '-=0.2',
        );
    };

    gsap.delayedCall(LECTURA, girar);
  });
}

/**
 * `data-giratorio-arrastre` — el modelo lo gira el visitante, y solo él.
 *
 * **El cursor manda sin necesidad de pulsar, y manda 1:1.** La posición
 * horizontal del puntero dentro de la sección se corresponde con un punto
 * exacto del recorrido. Nada de amortiguar el seguimiento: un amortiguado deja
 * el modelo por detrás de la mano y, peor, lo deja rodando un instante después
 * de que el cursor se para. Se siente desincronizado, que es justo lo que hay
 * que evitar en un control directo.
 *
 * Lo único que se suaviza es el **enganche**: al entrar en la sección con el
 * cursor lejos del punto actual, saltar de golpe sería feo, así que el modelo
 * recorre esa distancia en un cuarto de segundo y a partir de ahí queda pegado
 * al puntero. En reposo se queda quieto, sin competir con el titular.
 *
 * **No se interpola entre fotogramas.** Hubo una versión que fundía el
 * fotograma actual con el siguiente para suavizar el giro automático; medido,
 * ese fundido costaba un 36 % de nitidez y dejaba los culmos con doble borde.
 * Con el movimiento atado a la mano el fundido sobra: se dibuja siempre el
 * fotograma más cercano, que está nítido al 100 %, y la continuidad la pone el
 * gesto. Es como funciona cualquier visor de 360° de producto.
 *
 * **El arrastre va pegado al cursor y nunca cambia de sentido por su cuenta.**
 * Eso obliga a tratar los extremos distinto según el gesto:
 *
 * - La inercia de un arrastre **rebota** en los extremos.
 * - El arrastre en sí **se topa**: llega al final y se queda ahí. Si rebotara,
 *   el modelo se devolvería con el cursor todavía yendo a la derecha.
 * - Con una vuelta de 360° de verdad no hay extremos: todo da la vuelta.
 *
 * El dibujo sale del ticker y no del `pointermove`: el puntero dispara varias
 * veces por fotograma y pintar en cada uno es trabajo tirado, además de que
 * descuadra la medida de velocidad.
 */
function giratorioArrastre(
  ctx: gsap.Context,
  root: ParentNode,
  conMovimiento: boolean,
  alSoltar: Soltar,
) {
  root.querySelectorAll<HTMLElement>('[data-giratorio-arrastre]').forEach((caja) => {
    const total = Number(caja.dataset.total);
    const lienzo = caja.querySelector<HTMLCanvasElement>('[data-lienzo]');
    if (!lienzo || !total) return;
    const pincel = lienzo.getContext('2d');
    if (!pincel) return;

    /** Sin vuelta completa: la secuencia tiene principio y final. */
    const topes = caja.dataset.vaiven !== undefined;
    const ultimo = total - 1;

    // La secuencia pesa un par de megas y vive en la portada. Se pide el
    // primer fotograma de inmediato —es el que se ve— y el resto cuando la
    // página ya cargó y el navegador está ocioso, para no competir por ancho
    // de banda con la fotografía de fondo, que es lo que mide el LCP.
    const cuadros: HTMLImageElement[] = Array.from({ length: total }, () => {
      const img = new Image();
      img.decoding = 'async';
      return img;
    });
    const pedir = (i: number) => {
      if (!cuadros[i].src) cuadros[i].src = `/modelo-360/modelo-${String(i).padStart(3, '0')}.webp`;
    };
    pedir(0);
    const pedirResto = () => {
      for (let i = 1; i < total; i++) pedir(i);
    };
    const ocioso = (window as any).requestIdleCallback ?? ((f: () => void) => setTimeout(f, 300));
    if (document.readyState === 'complete') ocioso(pedirResto);
    else window.addEventListener('load', () => ocioso(pedirResto), { once: true });

    let indice = 0;
    let dibujado = -1;

    function dibujar(forzar = false) {
      const n = ((Math.round(indice) % total) + total) % total;
      if (n === dibujado && !forzar) return;
      const img = cuadros[n];
      if (!img?.complete || !img.naturalWidth) return;
      dibujado = n;
      const { width: w, height: h } = lienzo!;
      pincel!.clearRect(0, 0, w, h);
      // `contain`: el modelo no se recorta, va sin fondo sobre la página.
      const escala = Math.min(w / img.naturalWidth, h / img.naturalHeight);
      const dw = img.naturalWidth * escala;
      const dh = img.naturalHeight * escala;
      pincel!.drawImage(img, (w - dw) / 2, (h - dh) / 2, dw, dh);
    }

    function dimensionar() {
      // Nunca más píxeles de los que trae la fuente. Pedirle al lienzo más
      // resolución de la que hay no inventa detalle: gasta memoria y relleno
      // para acabar interpolando igual, y encima estropea el dibujo, que se ve
      // blando. Con el tope, el lienzo se queda en 1:1 con el fotograma y la
      // ampliación —si el hueco es mayor— la hace el navegador de una vez,
      // sobre una imagen ya nítida.
      const fuente = cuadros[0]?.naturalWidth || 0;
      const ancho = lienzo!.clientWidth || 1;
      const techo = fuente ? fuente / ancho : Infinity;
      const dpr = Math.min(window.devicePixelRatio || 1, 2, techo);
      // Se mide el lienzo y no la caja: con el rótulo debajo, la caja es más
      // alta que el dibujo y el modelo saldría estirado.
      lienzo!.width = Math.round(ancho * dpr);
      lienzo!.height = Math.round(lienzo!.clientHeight * dpr);
      dibujar(true);
    }
    dimensionar();
    window.addEventListener('resize', dimensionar);
    alSoltar(() => window.removeEventListener('resize', dimensionar));
    cuadros[0].addEventListener('load', dimensionar, { once: true });

    /** Avance libre: rebota en los extremos o da la vuelta, según la fuente. */
    function correr(delta: number) {
      let v = indice + delta;
      if (!topes) {
        indice = ((v % total) + total) % total;
        return;
      }
      // El rebote se resuelve en bucle por si un paso largo pasa de largo el
      // extremo: con dos rebotes seguidos el modelo se quedaría fuera de rango.
      for (let g = 0; g < 4; g++) {
        if (v > ultimo) v = 2 * ultimo - v;
        else if (v < 0) v = -v;
        else break;
      }
      indice = Math.min(ultimo, Math.max(0, v));
    }

    /** Avance del gesto: se topa en los extremos, nunca se devuelve. */
    function llevar(v: number) {
      indice = topes ? Math.min(ultimo, Math.max(0, v)) : ((v % total) + total) % total;
    }

    let arrastrando = false;
    let inercia = 0;

    // Zona de escucha: la sección entera y no solo el lienzo. El visitante no
    // tiene que acertarle al modelo; le basta con recorrer la portada.
    const zona = (caja.closest('section') as HTMLElement) ?? caja;
    /** Punto del recorrido que pide el cursor, o null si no hay cursor dentro. */
    let pedido: number | null = null;
    /** Ya alcanzó al cursor: a partir de aquí va pegado, sin retraso. */
    let enganchado = false;

    zona.addEventListener('pointermove', (e) => {
      // En táctil no hay cursor que seguir: ahí manda el arrastre.
      if (e.pointerType === 'touch') return;
      const r = zona.getBoundingClientRect();
      const t = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
      pedido = t * ultimo;
    });
    zona.addEventListener('pointerleave', () => {
      pedido = null;
      enganchado = false;
    });

    /* El bucle se guarda en una variable para poder quitarlo. Anónimo dentro
       de `gsap.ticker.add` no había forma de soltarlo, y era el que seguía
       corriendo después de cambiar de modo. */
    const bucle = (_t: number, dt: number) => {
      const s = Math.min(dt, 50) / 1000;

      if (arrastrando) {
        llevar(objetivo);
        dibujar();
        return;
      }

      if (pedido !== null) {
        inercia = 0;
        if (enganchado) {
          // Pegado al cursor: si el cursor no se mueve, el modelo tampoco.
          indice = pedido;
        } else {
          // Enganche: recorre de una vez la distancia hasta el cursor y se
          // engancha en cuanto está a menos de medio fotograma.
          indice += (pedido - indice) * (1 - Math.exp(-s / 0.09));
          if (Math.abs(pedido - indice) < 0.5) {
            indice = pedido;
            enganchado = true;
          }
        }
        dibujar();
        return;
      }

      if (inercia) {
        correr(inercia * s);
        // Frenado exponencial. En un extremo con topes la inercia se apaga:
        // rebotar contra el tope justo después de soltar se siente como un
        // rechazo, no como que el modelo sigue rodando.
        inercia *= Math.exp(-s / 0.4);
        if (topes && (indice <= 0 || indice >= ultimo)) inercia = 0;
        if (Math.abs(inercia) < 0.35) inercia = 0;
        dibujar();
      }
    };
    gsap.ticker.add(bucle);
    alSoltar(() => gsap.ticker.remove(bucle));

    let objetivo = 0;
    let xInicial = 0;
    let iInicial = 0;
    let ultimaX = 0;
    let ultimoT = 0;
    let porPixel = 0;

    /* EN TÁCTIL EL GESTO SE DECIDE, NO SE TOMA.
       El modelo ocupa media portada en celular. Agarrando el dedo en cuanto lo
       posa —que es lo que hacía `setPointerCapture` en el `pointerdown`, con
       `touch-action: none` debajo— la página dejaba de desplazarse: el visitante
       arrastraba hacia abajo sobre el kiosco y no pasaba nada.

       Ahora el dedo entra en observación: se mira hacia dónde sale. Si sale de
       lado, el giro se queda el gesto; si sale hacia arriba o abajo, se retira y
       el desplazamiento sigue siendo del navegador. Con `touch-action: pan-y` el
       navegador desplaza mientras tanto sin esperar a que decidamos, así que no
       hay retardo. Con ratón no hay nada que decidir: agarra al pulsar. */
    let vigilando = false;
    let yInicial = 0;

    function agarrar(e: PointerEvent) {
      arrastrando = true;
      inercia = 0;
      // Un recorrido entero por cada ancho y cuarto de arrastre; medido contra
      // el lienzo para que el gesto cueste lo mismo en un portátil que en un
      // celular. Se calcula al agarrar y no en cada movimiento: si la caja
      // cambiara de ancho a mitad del gesto, el modelo pegaría un tirón.
      porPixel = total / (lienzo!.clientWidth * 1.25);
      objetivo = iInicial = indice;
      xInicial = ultimaX = e.clientX;
      ultimoT = e.timeStamp;
      lienzo!.setPointerCapture(e.pointerId);
    }

    lienzo.addEventListener('pointerdown', (e) => {
      if (e.pointerType === 'touch') {
        vigilando = true;
        xInicial = e.clientX;
        yInicial = e.clientY;
        return;
      }
      agarrar(e);
      e.preventDefault();
    });

    lienzo.addEventListener('pointermove', (e) => {
      if (vigilando) {
        const dx = e.clientX - xInicial;
        const dy = e.clientY - yInicial;
        // 8 px: por debajo el gesto todavía no tiene dirección y decidir ahí
        // acierta la mitad de las veces.
        if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
        vigilando = false;
        // Sale hacia arriba o abajo: es un desplazamiento de página, no un giro.
        if (Math.abs(dy) >= Math.abs(dx)) return;
        agarrar(e);
      }
      if (!arrastrando) return;
      objetivo = iInicial + (e.clientX - xInicial) * porPixel;

      const dt = e.timeStamp - ultimoT;
      if (dt > 0) {
        // Fotogramas por segundo, que es la unidad del ticker. Media móvil
        // para que el último tirón del puntero no mande sobre todo el gesto.
        const v = ((e.clientX - ultimaX) * porPixel * 1000) / dt;
        inercia = inercia * 0.6 + v * 0.4;
        ultimaX = e.clientX;
        ultimoT = e.timeStamp;
      }
    });

    const soltar = (e: PointerEvent) => {
      vigilando = false;
      if (!arrastrando) return;
      arrastrando = false;
      lienzo.releasePointerCapture?.(e.pointerId);
      if (!conMovimiento) inercia = 0;
      // Soltar quieto en un extremo no deja inercia que rebote de inmediato.
      if (topes && (indice <= 0 || indice >= ultimo)) inercia = 0;
    };
    lienzo.addEventListener('pointerup', soltar);
    lienzo.addEventListener('pointercancel', soltar);
    // Y también en la ventana: si el visitante arrastra hasta fuera del
    // navegador y suelta ahí, el `pointerup` no llega al lienzo y el gesto se
    // quedaría abierto para siempre —el modelo, congelado—. `lostpointercapture`
    // cubre además el caso de que el sistema le quite la captura.
    window.addEventListener('pointerup', soltar);
    window.addEventListener('pointercancel', soltar);
    lienzo.addEventListener('lostpointercapture', soltar);
    alSoltar(() => {
      window.removeEventListener('pointerup', soltar);
      window.removeEventListener('pointercancel', soltar);
    });
  });
}

/**
 * `data-visor` — el panel del calificador responde a lo que el visitante mira.
 *
 * Al enfocar una opción, la isla emite `calificador:vista` y aquí se cruza a
 * la vista que corresponde. El cruce es corto: es una respuesta, no una
 * transición de escena.
 *
 * Con movimiento reducido el cruce es instantáneo, pero ocurre: lo que el panel
 * muestra es qué significa cada opción, y eso es información, no adorno. Antes
 * el visor entero se quedaba fuera de esa rama y el panel no se movía nunca.
 */
function visorCalificador(ctx: gsap.Context, root: ParentNode, animar: boolean) {
  root.querySelectorAll<HTMLElement>('[data-visor-raiz]').forEach((raiz) => {
    const visor = raiz.querySelector<HTMLElement>('[data-visor]');
    if (!visor) return;

    const vistas = new Map<string, HTMLElement>();
    visor.querySelectorAll<HTMLElement>('[data-vista]').forEach((v) => {
      vistas.set(v.dataset.vista!, v);
    });

    let actual = 'reposo';

    raiz.addEventListener('calificador:vista', (e) => {
      const pedida = (e as CustomEvent).detail?.vista ?? 'reposo';
      const destino = vistas.has(pedida) ? pedida : 'reposo';
      if (destino === actual) return;

      const sale = vistas.get(actual)!;
      const entra = vistas.get(destino)!;
      actual = destino;

      gsap.killTweensOf([sale, entra]);

      if (!animar) {
        sale.classList.remove('activa');
        entra.classList.add('activa');
        gsap.set([sale, entra], { clearProps: 'all' });
        return;
      }

      gsap.to(sale, {
        opacity: 0,
        duration: 0.18,
        ease: 'power2.in',
        onComplete: () => sale.classList.remove('activa'),
      });
      entra.classList.add('activa');
      gsap.fromTo(
        entra,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out', delay: 0.08 },
      );
    });

    // Las vistas `zona:<municipio>` son el mismo caso que las de pieza, con un
    // matiz que decide la forma: el mapa no es un elemento por zona sino uno
    // solo, y lo que cambia entre opciones es cuál punto está encendido. De ahí
    // los dos estados en dos sitios distintos —`.activa` en el envoltorio dice
    // si el mapa está, `data-zona` en él mismo dice a quién señala—: recorrer
    // las seis opciones con el cursor no vuelve a animar el mapa entero, que se
    // sentiría como un parpadeo, y el resaltado lo resuelve el CSS solo.
    const mapa = raiz.querySelector<HTMLElement>('[data-mapa]');
    if (mapa) {
      let zonaActual: string | null = null;

      raiz.addEventListener('calificador:vista', (e) => {
        const pedida: string | null = (e as CustomEvent).detail?.vista ?? null;
        const zona = pedida?.startsWith('zona:') ? pedida.slice(5) : null;
        if (zona === zonaActual) return;
        const estaba = zonaActual !== null;
        zonaActual = zona;

        if (zona) mapa.dataset.zona = zona;
        else delete mapa.dataset.zona;

        // Y se marca qué está encendido, para que el CSS no tenga que traer
        // escrita la lista de municipios. El punto lleva el nombre de su
        // municipio, así que de él sale también qué polígono resaltar —y por
        // eso Bruselas, que es corregimiento de Pitalito, ilumina Pitalito
        // entero sin que haya que decirlo en ningún sitio—.
        mapa.querySelectorAll('.activa').forEach((e) => e.classList.remove('activa'));
        const punto = zona
          ? mapa.querySelector<SVGElement>(`[data-punto="${zona}"]`)
          : null;
        if (punto) {
          punto.classList.add('activa');
          const muni = punto.dataset.muni;
          if (muni) mapa.querySelector(`path[data-muni="${muni}"]`)?.classList.add('activa');
        }

        // De un municipio a otro el mapa ya está puesto: solo cambió el
        // atributo y el CSS hace el resto. Aquí solo se anima entrar y salir.
        if (estaba === (zona !== null)) return;

        gsap.killTweensOf(mapa);

        if (!animar) {
          mapa.classList.toggle('activa', zona !== null);
          gsap.set(mapa, { clearProps: 'all' });
          return;
        }

        if (zona) {
          mapa.classList.add('activa');
          gsap.fromTo(
            mapa,
            { opacity: 0, y: 12 },
            { opacity: 1, y: 0, duration: 0.28, ease: 'power2.out' },
          );
        } else {
          gsap.to(mapa, {
            opacity: 0,
            duration: 0.16,
            ease: 'power2.in',
            onComplete: () => mapa.classList.remove('activa'),
          });
        }
      });
    }

    // Las vistas `fecha:<tramo>` son el calendario, y funcionan igual que el
    // mapa: un solo dibujo que entra una vez y por dentro enciende lo que toca.
    // El rango de semanas de cada tramo viaja en el propio elemento —lo escribe
    // el componente al lado de las opciones— para que cambiar una pregunta no
    // obligue a tocar también este archivo.
    const cal = raiz.querySelector<HTMLElement>('[data-calendario]');
    if (cal) {
      const tramos: Record<string, number[]> = JSON.parse(cal.dataset.tramos || '{}');
      let tramoActual: string | null = null;

      raiz.addEventListener('calificador:vista', (e) => {
        const pedida: string | null = (e as CustomEvent).detail?.vista ?? null;
        const tramo = pedida?.startsWith('fecha:') ? pedida.slice(6) : null;
        if (tramo === tramoActual) return;
        const estaba = tramoActual !== null;
        tramoActual = tramo;

        if (tramo) cal.dataset.tramo = tramo;
        else delete cal.dataset.tramo;

        cal.querySelectorAll('.semana.activa').forEach((s) => s.classList.remove('activa'));
        const rango = tramo ? tramos[tramo] : null;
        if (rango && rango.length === 2) {
          const [a, b] = rango;
          cal.querySelectorAll<SVGElement>('[data-semana]').forEach((sem) => {
            const n = Number(sem.dataset.semana);
            if (n >= a && n <= b) sem.classList.add('activa');
          });
        }

        // Entrar y salir se anima; cambiar de tramo lo resuelve el CSS solo.
        if (estaba === (tramo !== null)) return;
        gsap.killTweensOf(cal);

        if (!animar) {
          cal.classList.toggle('activa', tramo !== null);
          gsap.set(cal, { clearProps: 'all' });
          return;
        }
        if (tramo) {
          cal.classList.add('activa');
          gsap.fromTo(
            cal,
            { opacity: 0, y: 12 },
            { opacity: 1, y: 0, duration: 0.28, ease: 'power2.out' },
          );
        } else {
          gsap.to(cal, {
            opacity: 0,
            duration: 0.16,
            ease: 'power2.in',
            onComplete: () => cal.classList.remove('activa'),
          });
        }
      });
    }

    // Las vistas `pieza:<slug>` no entran por el cruce de arriba: no reemplazan
    // el panel, se abren debajo del texto —el titular sigue ahí, porque la
    // pieza lo ilustra en vez de contestar otra cosa—. Para el cruce anterior
    // no existen, así que deja el panel en reposo, que es justo lo que hace
    // falta.
    const galeria = raiz.querySelector<HTMLElement>('[data-piezas]');
    if (!galeria) return;

    const piezas = new Map<string, HTMLElement>();
    galeria.querySelectorAll<HTMLElement>('[data-pieza]').forEach((f) => {
      piezas.set(f.dataset.pieza!, f);
    });

    let piezaActual: string | null = null;

    raiz.addEventListener('calificador:vista', (e) => {
      const pedida: string | null = (e as CustomEvent).detail?.vista ?? null;
      const slug = pedida?.startsWith('pieza:') ? pedida.slice(6) : null;
      const destino = slug && piezas.has(slug) ? slug : null;
      if (destino === piezaActual) return;

      const sale = piezaActual ? piezas.get(piezaActual)! : null;
      piezaActual = destino;
      const entra = destino ? piezas.get(destino)! : null;

      gsap.killTweensOf([sale, entra].filter(Boolean) as HTMLElement[]);

      if (!animar) {
        sale?.classList.remove('activa');
        entra?.classList.add('activa');
        gsap.set([sale, entra].filter(Boolean) as HTMLElement[], { clearProps: 'all' });
        return;
      }

      if (sale) {
        gsap.to(sale, {
          opacity: 0,
          duration: 0.16,
          ease: 'power2.in',
          onComplete: () => sale.classList.remove('activa'),
        });
      }
      if (entra) {
        entra.classList.add('activa');
        gsap.fromTo(
          entra,
          { opacity: 0, y: 12 },
          { opacity: 1, y: 0, duration: 0.28, ease: 'power2.out' },
        );
      }
    });
  });
}

/**
 * `data-giratorio` — el modelo gira sobre sí mismo, fotograma a fotograma.
 *
 * Solo gira mientras su vista está a la vista: fuera de ella el bucle se para
 * y deja de consumir cuadros.
 */
function giratorio(ctx: gsap.Context, root: ParentNode, alSoltar: Soltar) {
  root.querySelectorAll<HTMLElement>('[data-giratorio]').forEach((caja) => {
    const total = Number(caja.dataset.total);
    const lienzo = caja.querySelector<HTMLCanvasElement>('[data-lienzo]');
    if (!lienzo || !total) return;
    const pincel = lienzo.getContext('2d');
    if (!pincel) return;

    const cuadros: HTMLImageElement[] = [];
    for (let i = 0; i < total; i++) {
      const img = new Image();
      img.decoding = 'async';
      img.src = `/modelo-360/modelo-${String(i).padStart(3, '0')}.webp`;
      cuadros.push(img);
    }

    function dimensionar() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      lienzo!.width = Math.round(caja.offsetWidth * dpr);
      lienzo!.height = Math.round(caja.offsetHeight * dpr);
    }
    dimensionar();
    window.addEventListener('resize', dimensionar);
    alSoltar(() => window.removeEventListener('resize', dimensionar));

    const vaiven = caja.dataset.vaiven !== undefined;
    const periodo = vaiven ? 2 * total - 2 : total;

    const giro = { i: 0 };
    const bucle = gsap.to(giro, {
      i: periodo,
      duration: periodo / 18, // ~18 fotogramas por segundo
      ease: 'none',
      repeat: -1,
      paused: true,
      onUpdate: () => {
        const img = cuadros[fotograma(giro.i, total, vaiven)];
        if (!img?.complete || !img.naturalWidth) return;
        const { width: w, height: h } = lienzo!;
        pincel!.clearRect(0, 0, w, h);
        // `contain`: el modelo no se recorta, va sin fondo sobre la página.
        const escala = Math.min(w / img.naturalWidth, h / img.naturalHeight);
        const dw = img.naturalWidth * escala;
        const dh = img.naturalHeight * escala;
        pincel!.drawImage(img, (w - dw) / 2, (h - dh) / 2, dw, dh);
      },
    });

    // Solo gira mientras se ve.
    const vista = caja.closest<HTMLElement>('[data-vista]');
    if (vista) {
      new MutationObserver(() => {
        vista.classList.contains('activa') ? bucle.play() : bucle.pause();
      }).observe(vista, { attributes: true, attributeFilter: ['class'] });
    } else {
      bucle.play();
    }
  });
}

/**
 * `data-deriva` — el fondo fotográfico respira.
 *
 * Escala y desplazamiento mínimos en treinta segundos: lo justo para que el
 * fondo no se sienta congelado. Cualquier cosa más rápida compite con el
 * formulario que va encima.
 */
function deriva(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-deriva]').forEach((capa) => {
    gsap.to(capa, {
      scale: 1.07,
      xPercent: -1.6,
      yPercent: -1.2,
      duration: 30,
      ease: 'sine.inOut',
      repeat: -1,
      yoyo: true,
    });
  });
}

/**
 * `data-marco` — el marco de guadua se arma antes de descubrir la foto.
 *
 * La secuencia es la del oficio, no un efecto: se colocan los cuatro elementos
 * girando, se amarran las esquinas y solo entonces aparece lo que enmarcan.
 * Por eso los lados crecen desde la esquina donde termina el anterior.
 */
function marcos(ctx: gsap.Context, root: ParentNode) {
  const marcos = root.querySelectorAll<HTMLElement>('[data-marco]');
  if (!marcos.length) return;

  ScrollTrigger.batch(Array.from(marcos), {
    start: 'top 88%',
    once: true,
    onEnter: (lote) =>
      lote.forEach((marco, i) => {
        const lados = marco.querySelectorAll('[data-lado]');
        const nudos = marco.querySelectorAll('[data-nudo]');
        const amarres = marco.querySelectorAll('[data-amarre] g');
        const ventana = marco.querySelector('[data-ventana]');
        const img = marco.querySelector('img');

        const tl = gsap.timeline({ delay: i * 0.08 });

        // Los cuatro elementos, uno tras otro, girando alrededor del marco.
        lados.forEach((lado, j) => {
          const horizontal = j === 0 || j === 2;
          tl.to(
            lado,
            {
              [horizontal ? 'scaleX' : 'scaleY']: 1,
              duration: 0.34,
              ease: 'power2.inOut',
            },
            j * 0.24,
          );
        });

        tl.to(nudos, { scale: 1, duration: 0.3, ease: 'back.out(2)', stagger: 0.02 }, 0.5)
          // Los amarres se atan cuando las piezas ya están puestas.
          .to(
            amarres,
            { opacity: 1, scale: 1, duration: 0.3, ease: 'power2.out', stagger: 0.06 },
            0.85,
          )
          .fromTo(
            amarres,
            { scale: 0.4 },
            { scale: 1, duration: 0.4, ease: 'back.out(2.2)', stagger: 0.06 },
            0.85,
          )
          // Y la foto se descubre dentro del marco ya armado.
          .to(ventana, { clipPath: 'inset(0%)', duration: 0.8, ease: 'power3.inOut' }, 1.0);

        if (img) tl.from(img, { scale: 1.16, duration: 1.1, ease: 'power3.out' }, 1.0);
      }),
  });
}

/* ------------------------------------------------------------------ *
 * Movimiento ligado al scroll
 * ------------------------------------------------------------------ */

/**
 * `data-nav` — la cabecera se despega de la página en cuanto se baja.
 *
 * Es el único elemento del sitio que se superpone al contenido todo el rato,
 * así que es donde más se nota si hay o no un eje Z: arriba del todo va a ras,
 * sin sombra y con la marca a tamaño completo; en cuanto empieza el scroll se
 * compacta y proyecta sombra, y el contenido pasa por debajo en vez de junto a
 * ella. No anima alto ni padding —eso recalcularía layout en cada cuadro—:
 * la clase cambia una vez y el CSS hace la transición.
 */
function navCompacta(ctx: gsap.Context, root: ParentNode) {
  const nav = root.querySelector<HTMLElement>('[data-nav]');
  if (!nav) return;

  ScrollTrigger.create({
    start: 'top -12',
    end: 99999,
    onToggle: ({ isActive }) => nav.classList.toggle('compacta', isActive),
  });
}

/** `data-parallax="N"` — la foto se mueve más lento que el scroll, dentro de su marco. */
function parallax(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-parallax]').forEach((img) => {
    const recorrido = Number(img.dataset.parallax) || 12;
    gsap.fromTo(
      img,
      { yPercent: -recorrido / 2 },
      {
        yPercent: recorrido / 2,
        ease: 'none',
        scrollTrigger: {
          trigger: img.closest('[data-parallax-marco]') ?? img.parentElement ?? img,
          start: 'top bottom',
          end: 'bottom top',
          scrub: true,
        },
      },
    );
  });
}

/**
 * `data-curado` — el momento narrativo del sitio.
 *
 * La sección se fija y, mientras se hace scroll, la caña pasa de verde a
 * curada: cambia el tinte de la textura y el color del texto. Es el mismo
 * proceso que sufre el material al inmunizarse, contado con el scroll como
 * línea de tiempo.
 */
function curado(ctx: gsap.Context, root: ParentNode) {
  const seccion = root.querySelector<HTMLElement>('[data-curado]');
  if (!seccion) return;

  const verde = seccion.querySelector<HTMLElement>('[data-capa="verde"]');
  const curada = seccion.querySelector<HTMLElement>('[data-capa="curada"]');
  const pasos = seccion.querySelectorAll<HTMLElement>('[data-paso]');

  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: seccion,
      start: 'top top',
      end: '+=260%',
      pin: true,
      scrub: 1,
      anticipatePin: 1,
    },
  });

  // Cada etapa ocupa un tramo propio y no se pisa con la siguiente: el saliente
  // termina de irse antes de que entre el que sigue. Con `scrub` un solapamiento
  // de medio tramo deja dos textos legibles a la vez y se lee como un error.
  const TRAMO = 1;      // duración de cada etapa en la línea de tiempo
  const CAMBIO = 0.32;  // lo que tarda en entrar o salir
  const INICIO = 0.4;   // aire antes de la primera etapa
  pasos.forEach((paso, i) => {
    const inicio = INICIO + i * TRAMO;
    tl.fromTo(
      paso,
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: CAMBIO, ease: 'power2.out' },
      inicio,
    );
    if (i < pasos.length - 1) {
      tl.to(
        paso,
        { opacity: 0, y: -24, duration: CAMBIO, ease: 'power2.in' },
        inicio + TRAMO - CAMBIO,
      );
    }
  });

  // El curado se reparte a lo largo de las cuatro etapas, no al principio:
  // la caña entra verde en el corte y sale curada en el secado. Si el
  // fundido se resuelve en el primer tramo, la sección deja de contar nada.
  const largo = INICIO + pasos.length * TRAMO;
  tl.to(verde, { opacity: 0, ease: 'none', duration: largo - INICIO * 2 }, INICIO)
    .fromTo(
      curada,
      { opacity: 0 },
      { opacity: 1, ease: 'none', duration: largo - INICIO * 2 },
      INICIO,
    );
}

/**
 * `data-cierre` — el guadual que se abre debajo del pie.
 *
 * La página termina en el pie; quien siga bajando lo abre. El tramo se fija y
 * el scroll reproduce la secuencia AL REVÉS: se baja del dosel al brote, que
 * es el movimiento contrario al del resto del sitio.
 *
 * Se pinta en `<canvas>` y no con un `<video>` al que se le mueve
 * `currentTime`: en iOS el seek no es fiable y el barrido sale a tirones.
 */
function cierreGuadual(ctx: gsap.Context, root: ParentNode, alSoltar: Soltar) {
  const cierre = root.querySelector<HTMLElement>('[data-cierre]');
  if (!cierre) return;

  const total = Number(cierre.dataset.total);
  const escena = cierre.querySelector<HTMLElement>('.escena');
  const guadual = cierre.querySelector<HTMLElement>('[data-guadual]');
  const lienzo = cierre.querySelector<HTMLCanvasElement>('[data-lienzo]');
  const poster = cierre.querySelector<HTMLImageElement>('[data-poster]');
  const leyenda = cierre.querySelector<HTMLElement>('[data-leyenda]');
  const pie = cierre.querySelector<HTMLElement>('[data-pie-envoltura]');
  if (!escena || !guadual || !lienzo || !pie || !total) return;

  const pincel = lienzo.getContext('2d', { alpha: false });
  if (!pincel) return;

  const cuadros: HTMLImageElement[] = [];
  let actual = -1;

  /** Replica `object-fit: cover` sobre el lienzo. */
  function pintar(i: number) {
    const img = cuadros[i];
    if (!img?.complete || !img.naturalWidth) return;
    actual = i;
    const { width: w, height: h } = lienzo!;
    const escala = Math.max(w / img.naturalWidth, h / img.naturalHeight);
    const dw = img.naturalWidth * escala;
    const dh = img.naturalHeight * escala;
    pincel!.drawImage(img, (w - dw) / 2, (h - dh) / 2, dw, dh);
  }

  function dimensionar() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    lienzo!.width = Math.round(guadual!.offsetWidth * dpr);
    lienzo!.height = Math.round(guadual!.offsetHeight * dpr);
    if (actual >= 0) pintar(actual);
  }

  // La secuencia solo se descarga cuando el pie ya está cerca: son 4,5 MB y
  // la mayoría de los visitantes no llega hasta aquí.
  let pedida = false;
  function cargar() {
    if (pedida) return;
    pedida = true;
    for (let i = 0; i < total; i++) {
      const img = new Image();
      img.decoding = 'async';
      img.src = `/secuencia/guadual-${String(i).padStart(3, '0')}.webp`;
      // El último fotograma es el que abre el cierre: en cuanto está, se pinta.
      if (i === total - 1) {
        img.onload = () => {
          dimensionar();
          pintar(total - 1);
          lienzo!.classList.add('activo');
          if (poster) poster.style.opacity = '0';
        };
      }
      cuadros.push(img);
    }
  }

  ScrollTrigger.create({
    trigger: cierre,
    start: 'top bottom+=600',
    once: true,
    onEnter: cargar,
  });

  window.addEventListener('resize', dimensionar);
  alSoltar(() => window.removeEventListener('resize', dimensionar));

  const avance = { p: 0 };
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: cierre,
      start: 'top top',
      end: '+=300%',
      pin: escena,
      scrub: 0.5,
      anticipatePin: 1,
      // El tramo es reversible: al subir, el guadual se recoge y vuelve el pie.
      onUpdate: (self) => {
        // El primer tercio abre el cierre; el resto reproduce la secuencia.
        const abierto = Math.max(0, (self.progress - 0.18) / 0.82);
        avance.p = abierto;
        // Al revés: del dosel al brote.
        const i = Math.round((1 - abierto) * (total - 1));
        if (i !== actual) pintar(i);
      },
    },
  });

  tl.to(pie, { opacity: 0, y: -30, duration: 0.16, ease: 'power2.in' }, 0)
    // Crece hacia abajo descubriendo la escena, no aparece por fundido.
    .to(guadual, { clipPath: 'inset(0 0 0% 0)', duration: 0.26, ease: 'power2.inOut' }, 0.04)
    .to(leyenda, { opacity: 1, duration: 0.12 }, 0.3)
    .to(leyenda, { opacity: 0, duration: 0.12 }, 0.88);
}

/** Barra de avance de lectura: se llena como una caña que crece. */
function avance(ctx: gsap.Context, root: ParentNode) {
  const barra = root.querySelector<HTMLElement>('[data-avance]');
  if (!barra) return;

  gsap.to(barra, {
    scaleX: 1,
    ease: 'none',
    scrollTrigger: { start: 0, end: 'max', scrub: 0.3 },
  });
}

/* ------------------------------------------------------------------ *
 * Arranque
 * ------------------------------------------------------------------ */

/**
 * La llamada flotante se retira mientras el calificador está en pantalla.
 *
 * En celular el botón naranja vive fijo abajo y ocupa una franja de la ventana
 * todo el rato. Dentro del calificador eso sobra por partida doble: el
 * visitante ya está en el embudo —a donde el botón lleva— y la franja tapa
 * justo la última pregunta y el botón de enviar.
 *
 * Es una clase en el `body` y no una animación de GSAP porque tiene que valer
 * también con movimiento reducido: ahí el botón no se desliza, desaparece, pero
 * estorbar sigue estorbando igual.
 */
function llamadaFlotante(root: ParentNode): (() => void) | undefined {
  const seccion = root.querySelector('#calificador');
  if (!seccion) return;
  const ojo = new IntersectionObserver(
    ([e]) => document.body.classList.toggle('en-calificador', e.isIntersecting),
    // Un tercio de la sección a la vista: el visitante ya está leyendo la
    // pregunta, no pasando de largo.
    { threshold: 0.33 },
  );
  ojo.observe(seccion);
  return () => {
    ojo.disconnect();
    document.body.classList.remove('en-calificador');
  };
}

/* El módulo se evalúa una sola vez aunque el DOM se sustituya en cada
   navegación (ver Base.astro), así que esta bandera distingue la carga en frío
   —la única que lleva splash y, por tanto, obertura— de las que vienen después.
   Ver `oberturaYaPuesta`. */
let primeraCarga = true;

export function iniciarMovimiento(root: ParentNode = document) {
  const esPrimeraCarga = primeraCarga;
  primeraCarga = false;
  const mm = gsap.matchMedia();
  const soltarLlamada = llamadaFlotante(root);

  mm.add(
    {
      conMovimiento: '(prefers-reduced-motion: no-preference)',
      sinMovimiento: '(prefers-reduced-motion: reduce)',
      escritorio: '(min-width: 781px)',
    },
    (contexto) => {
      const { conMovimiento, escritorio } = contexto.conditions!;

      /* Lo que este montaje deja suelto por el mundo y hay que recoger al
         desmontarlo. Local a cada condición de `matchMedia` y no global al
         módulo: al cruzar el punto de ruptura de escritorio, GSAP revierte una
         condición y monta la otra, y con una lista compartida la que se monta
         borraría los apuntes de la que se va. Ver `Soltar`. */
      const sueltas: (() => void)[] = [];
      const alSoltar: Soltar = (fn) => sueltas.push(fn);

      // Con movimiento reducido todo queda visible y quieto. Es una versión
      // legítima del sitio, no una degradada.
      if (!conMovimiento) {
        root.querySelectorAll<HTMLElement>(
          '[data-revelar-texto], [data-revelar-palabras], [data-voltear]',
        ).forEach((el) => (el.style.visibility = 'visible'));
        gsap.set('[data-capa="curada"]', { opacity: 1 });
        gsap.set('[data-capa="verde"], [data-paso]', { clearProps: 'all' });
        // La obertura se salta entera, pero su estado inicial vive en el CSS:
        // hay que devolver la portada a la vista con estilo en línea.
        gsap.set('[data-alza]', { opacity: 1, y: 0, scale: 1 });
        // Las juntas se ven enteras: el trazado era el gesto, no la pieza.
        gsap.set('.nudo', { '--nudo-regla': 1, '--nudo-marca': 1 });
        // El arrastre no es adorno: es el único modo de ver el modelo por
        // detrás. Se mantiene, sin giro de cortesía ni inercia.
        giratorioArrastre(contexto, root, false, alSoltar);
        rotante(contexto, root, false);
        indiceObra(contexto, root, false);
        // El panel del calificador cruza igual, sin fundido: es la respuesta a
        // lo que el visitante está mirando.
        visorCalificador(contexto, root, false);
        return () => sueltas.forEach((soltar) => soltar());
      }

      if (esPrimeraCarga) obertura(contexto, root);
      else oberturaYaPuesta(root);
      revelarTexto(contexto, root);
      revelarPalabras(contexto, root);
      voltearTexto(contexto, root);
      entradas(contexto, root);
      juntas(contexto, root);
      descubrirImagenes(contexto, root);
      morfo(contexto, root);
      marcos(contexto, root);
      deriva(contexto, root);
      visorCalificador(contexto, root, true);
      giratorio(contexto, root, alSoltar);
      giratorioArrastre(contexto, root, true, alSoltar);
      rotante(contexto, root, true);
      indiceObra(contexto, root, true);
      parallax(contexto, root);
      avance(contexto, root);
      navCompacta(contexto, root);

      // El fijado de sección solo en escritorio: en celular robar el scroll
      // durante 260vh se siente como que la página se trabó.
      // La secuencia son 72 imágenes, unos 4,5 MB: solo se descargan en
      // escritorio. En celular la portada se queda con el primer fotograma.
      if (escritorio) {
        curado(contexto, root);
        cierreGuadual(contexto, root, alSoltar);
      }
      else {
        gsap.set('[data-capa="curada"]', { opacity: 1 });
        gsap.set('[data-capa="verde"]', { opacity: 0 });
      }

      // GSAP llama a lo que devuelva este callback al revertir la condición.
      return () => sueltas.forEach((soltar) => soltar());
    },
  );

  // Las imágenes cambian el alto de la página al cargar; sin esto los
  // disparadores quedan calculados sobre posiciones viejas. Al rearmar tras una
  // navegación con ClientRouter el evento `load` ya pasó, así que se refresca
  // de una vez.
  if (document.readyState === 'complete') ScrollTrigger.refresh();
  else window.addEventListener('load', () => ScrollTrigger.refresh(), { once: true });

  return () => {
    soltarLlamada?.();
    mm.revert();
  };
}
