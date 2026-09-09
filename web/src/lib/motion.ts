import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { SplitText } from 'gsap/SplitText';
// `Observer` lee el gesto —rueda, dedo, arrastre— sin depender de que la
// página se desplace, y `ScrollToPlugin` permite animar la posición de scroll.
// Los dos son lo que convierte el carril en pasos discretos. Ver `horizontal`.
import { Observer } from 'gsap/Observer';
import { ScrollToPlugin } from 'gsap/ScrollToPlugin';

gsap.registerPlugin(ScrollTrigger, SplitText, Observer, ScrollToPlugin);

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
 * `data-horizontal` — LA SECCIÓN QUE SE RECORRE DE LADO.
 *
 * Una sección con más contenido del que cabe en una pantalla puede crecer
 * hacia abajo —y entonces es una corrida, varias pantallas de lectura libre— o
 * dejar de crecer y repartirse en paneles que se recorren de lado. Esto es lo
 * segundo: la sección se fija, y el desplazamiento vertical mueve el carril
 * horizontalmente. Cada panel es una parada.
 *
 * Es el patrón `containerAnimation` de ScrollTrigger, con sus dos reglas:
 *
 *   - `ease: 'none'` es OBLIGATORIO. Cualquier otra curva rompe la
 *     correspondencia 1:1 entre lo que se desplaza y lo que se mueve, y el
 *     carril adelanta o se retrasa respecto al dedo.
 *   - Se anima un HIJO y se fija el PADRE. Animar el propio elemento fijado es
 *     pedirle dos posiciones a la vez.
 *
 * Y el snap va aquí, en el tween de fuera. La documentación de GSAP avisa de
 * que un ScrollTrigger montado sobre `containerAnimation` no admite ni `pin`
 * ni `snap` —así que los paneles no pueden aterrizar cada uno por su cuenta—,
 * pero el tween que los arrastra sí: `1 / (paneles - 1)` reparte el recorrido
 * en tantos reposos como paneles hay. Ahí está el snap por panel.
 *
 * El recorrido se mide con funciones y no con números fijos: `end` y el
 * desplazamiento se vuelven a calcular en cada refresco, que es lo que hace
 * que sobreviva a un cambio de ancho de ventana y al cruce de modos.
 */
function horizontal(ctx: gsap.Context, root: ParentNode, alSoltar: Soltar) {
  root.querySelectorAll<HTMLElement>('[data-horizontal]').forEach((seccion) => {
    const carril = seccion.querySelector<HTMLElement>('[data-carril]');
    if (!carril) return;
    const paneles = carril.children.length;
    if (paneles < 2) return;

    // Lo que sobra del carril por fuera de su ventana: cuánto tiene que
    // viajar para que se vea el último panel.
    const sobra = () => Math.max(0, carril.scrollWidth - carril.parentElement!.clientWidth);

    // LO QUE CUESTA PASAR UN PANEL, y es la cifra que hace que esto se sienta
    // ligero o pesado. NO es el ancho del panel.
    //
    // Estuvo atado a `sobra()` —un píxel de scroll, un píxel de carril—, que
    // parece lo correcto y no lo es: el panel mide 1180 px de ancho y la
    // ventana 900 de alto, así que pasar una pieza costaba 1,38 pantallas y
    // las cinco del catálogo se comían 6,3 pantallas de recorrido. Medido en
    // Chromium a 1440×900.
    //
    // Atado a `PASO` —la unidad de recorrido del sitio— el precio es el mismo
    // para todos los paneles y el mismo que en el resto de la página. Un gesto
    // decidido de rueda o trackpad recorre una pieza y aterriza en ella.
    //
    // El carril se mueve entonces más rápido que el dedo, y eso está bien: la
    // correspondencia que hay que respetar es la del SNAP —un paso, un panel—,
    // no la de un píxel por píxel que nadie percibe.
    const recorrido = () => (paneles - 1) * paso();

    /* EL CRUCE DE OPACIDAD ENTRE PANELES.
     *
     * El que sale se apaga hacia el lado por el que se va y el que entra se
     * enciende viniendo del lado del gesto. No hace falta consultar la
     * dirección del scroll para eso: los paneles ya viajan en el sentido del
     * gesto, así que basta con que la opacidad dependa de LO LEJOS que está
     * cada panel del centro de la ventana. Lo que se aleja se apaga, y como
     * se aleja hacia donde el gesto lo empuja, el efecto sale solo y funciona
     * igual bajando que subiendo.
     *
     * Y se calcula sin tocar el DOM. Cada panel mide exactamente el ancho de
     * la ventana y no hay huecos, así que la distancia del panel `i` al centro,
     * medida en panteles, es `i - progreso × (paneles - 1)`. Ni un
     * `getBoundingClientRect` por fotograma: solo aritmética sobre el progreso
     * que ScrollTrigger ya trae.
     */
    const pintar = [...carril.children].map((p) =>
      gsap.quickSetter(p as HTMLElement, 'opacity'),
    );

    /* La curva del apagado, y el exponente importa.
     *
     * Lineal (`1 - d`) deja los dos paneles al 50 % justo a mitad de camino y
     * la pantalla se apaga entera un instante: el clásico bache del fundido
     * cruzado. Al cuadrado, a mitad de camino los dos van al 75 % y la
     * transición conserva su peso; el apagado se concentra en el último tramo,
     * cuando el panel ya está saliendo de cuadro y estorba menos. */
    const opacidadDe = (d: number) => Math.max(0, 1 - d * d);

    const cruzar = (progreso: number) => {
      const centro = progreso * (paneles - 1);
      for (let i = 0; i < pintar.length; i++) pintar[i](opacidadDe(Math.abs(i - centro)));
    };

    // El estado del paso a paso vive aquí arriba porque el trigger del propio
    // carril necesita poder encender y apagar la escucha desde su `onToggle`, y
    // ScrollTrigger captura sus callbacks al construirse.
    //
    // Hubo un trigger auxiliar para esto, con el mismo `start` y `end`, y no
    // servía: al estar la sección fijada por el primero, el segundo medía sobre
    // una geometría distinta y encendía y apagaba en momentos que no coincidían
    // con el fijado. El síntoma era que un gesto de cada dos se perdía.
    let indice = 0;

    /* EL CERROJO CADUCA SOLO, y por eso es una marca de tiempo y no un `true`.
     *
     * Un booleano que se levanta al empezar el viaje y se baja en el
     * `onComplete` deja la sección SORDA PARA SIEMPRE si ese `onComplete` no
     * llega —un tween interrumpido, un rearme a mitad de camino, un cambio de
     * modo—. No es hipotético: al probar la salida por los extremos, un viaje
     * que no se movía dejó el cerrojo echado y los gestos siguientes se
     * ignoraban sin que nada lo explicara.
     *
     * Con un instante de caducidad no hay estado que se pueda quedar mal: pase
     * lo que pase, pasado ese instante la sección vuelve a escuchar. */
    let sordoHasta = 0;
    const echarCerrojo = () => {
      sordoHasta = performance.now() + (VIAJE + RESPIRO) * 1000;
    };
    const sordo = () => performance.now() < sordoHasta;
    let mirador: Observer | undefined;

    const tomar = (progreso: number) => {
      mirador?.enable();
      // UN VIAJE EN MARCHA YA SABE A DÓNDE VA: nadie le corrige el índice.
      //
      // Sin esta línea se perdía un gesto de cada dos, y el motivo tardó en
      // verse. El `onToggle` del fijado se dispara al CRUZAR el arranque, o
      // sea en el primer fotograma del primer viaje, cuando el progreso
      // todavía vale ~0. `tomar` calculaba entonces índice 0 y machacaba el 1
      // que `irA` acababa de escribir, así que el gesto siguiente volvía a
      // pedir la pieza 2 —la que ya estaba en pantalla— y no pasaba nada.
      // Medido con el índice a la vista: `avanzar(1) indice=0 y=1527`.
      if (sordo()) return;
      indice = Math.round(progreso * (paneles - 1));
    };

    const viaje = gsap.to(carril, {
      x: () => -sobra(),
      ease: 'none',
      scrollTrigger: {
        trigger: seccion,
        onUpdate: (self) => cruzar(self.progress),
        // El primer panel tiene que estar encendido antes de que nadie llegue
        // a la sección: sin esto, el carril entra en negro y solo se enciende
        // al primer movimiento.
        onRefresh: (self) => cruzar(self.progress),
        start: 'top top',
        end: () => '+=' + recorrido(),
        pin: seccion,
        // SEGUIMIENTO DIRECTO, y aquí no admite matices.
        //
        // Estuvo en `scrub: 0.4` buscando suavidad y lo que produjo fue lo
        // contrario. Un `scrub` numérico es un retardo: el carril persigue al
        // scroll con ese alcance. Combinado con el acomodo del snap salen DOS
        // movimientos encadenados —el carril corriendo tras el scroll, y luego
        // el acomodo llevando el scroll a su destino—, y la pieza sigue
        // viajando después de que la página ya paró. Medido: 183 ms de desfase
        // entre el scroll llegando a su parada y el carril llegando a la suya,
        // más un tirón inicial de 660 px antes de que el acomodo empezara.
        //
        // Con `true` el carril es una función exacta de la posición de scroll,
        // así que la ÚNICA curva del movimiento es la del acomodo —que es donde
        // sí queremos elegancia, y donde ya está afinada—. Un movimiento, un
        // destino, sin nada persiguiendo a nada.
        //
        // El curado sí puede llevar `scrub: 1` porque allí no hay snap por
        // panel: el retardo suaviza un barrido continuo y no compite con
        // ningún aterrizaje.
        scrub: true,
        anticipatePin: 1,
        invalidateOnRefresh: true,
        // Sin `snap`: los pasos los da `Observer` más abajo, y un aterrizaje
        // automático competiría con ellos por la misma posición de scroll.
      },
    });

    /* ── EL PASO A PASO ───────────────────────────────────────────────────
     *
     * Un gesto, un panel. Mientras el paso está en marcha NO se escucha nada
     * más: la rueda queda sorda hasta que la pieza está puesta.
     *
     * Es lo que elimina el desfase por construcción en vez de perseguirlo
     * afinando curvas. Con `snap`, entre dos paradas existe un continuo de
     * posiciones intermedias, y la cola de inercia del trackpad —que sigue
     * entregando eventos medio segundo después de soltar— empuja dentro de ese
     * continuo mientras el acomodo intenta salir de él. Con pasos discretos ese
     * estado intermedio no existe: o estás en una pieza o estás viajando a la
     * siguiente, y viajando no se aceptan órdenes.
     *
     * LO QUE SE ANIMA ES LA POSICIÓN DE SCROLL, no el carril. Podría moverse el
     * carril directamente y sería más corto, pero entonces la posición de
     * scroll y lo que se ve dejarían de corresponderse: al salir de la sección,
     * al cambiar de tamaño la ventana o al rearmarse el movimiento en el cruce
     * de modos, la página sabría una cosa y la pantalla enseñaría otra.
     * Moviendo el scroll, el carril sigue siendo su función exacta —el `scrub`
     * de arriba— y el resto del sistema no se entera de nada.
     */
    // Se toma del propio tween y no se busca en el registro global: buscarlo
    // por `trigger` y `pin` fallaba en silencio —la función salía por aquí sin
    // crear nada y sin dejar rastro en la consola, y el carril se quedaba con
    // el `scrub` pero sin pasos—.
    const st = viaje.scrollTrigger;
    if (!st) return;

    const MARGEN = 2;
    const enRango = () =>
      window.scrollY >= st.start - MARGEN && window.scrollY <= st.end + MARGEN;

    const irA = (destino: number) => {
      echarCerrojo();
      indice = destino;
      gsap.to(window, {
        scrollTo: { y: st.start + destino * paso(), autoKill: false },
        duration: VIAJE,
        // La misma curva del resto de acomodos del sitio: entra sin tirón,
        // viaja parejo y se posa. Ver `paradas`.
        ease: 'power1.inOut',
      });
    };

    mirador = Observer.create({
      target: window,
      type: 'wheel,touch',
      // El gesto se consume aquí dentro: es lo que impide que la página se
      // desplace por su cuenta mientras se cambia de pieza.
      preventDefault: true,
      // Un umbral por encima del temblor de un trackpad en reposo, para que un
      // roce no cuente como paso.
      tolerance: 12,
      enabled: false,
      // `onDown` es BAJAR y `onUp` es SUBIR, y conviene dejarlo escrito porque
      // la intuición dice lo contrario: en `Observer` estos nombres describen
      // el sentido del gesto de la rueda —hacia abajo, hacia arriba—, no el del
      // contenido. Cambiados, el primer gesto hacia abajo llevaba a la portada.
      // Comprobado en Chromium: un evento con `deltaY: 120` dispara `onDown`.
      onDown: () => avanzar(1),
      onUp: () => avanzar(-1),
    });

    /* POR LOS EXTREMOS SE SALE, Y SE SALE IGUAL DE GOBERNADO.
     *
     * Pedir la pieza cero o la sexta significa que el visitante quiere irse de
     * la sección. La primera versión se limitaba a soltar la rueda y dejar que
     * la página se desplazara sola: el gesto que pedía salir no llevaba a
     * ninguna parte concreta, y hacía falta un segundo para que `paradas`
     * recogiera el siguiente y aterrizara. Dos gestos para una intención, y en
     * medio un tramo de scroll suelto.
     *
     * Ahora la salida es un paso más: el mismo viaje, el mismo bloqueo, y el
     * destino es la parada de la sección vecina. Un gesto arriba desde la
     * primera pieza deja la portada encuadrada de una vez.
     *
     * La posición de la vecina se calcula igual que en `paradas` —el arranque
     * de su pin si está fijada, su techo menos la barra si no—, porque tiene
     * que ser exactamente el mismo punto: si no, salir por aquí dejaría la
     * página medio píxel movida respecto a llegar por el camino normal, y el
     * aterrizaje de al lado se dispararía para corregirlo.
     */
    const vecinas = [...root.querySelectorAll<HTMLElement>('[data-parada]')];

    function salir(sentido: number) {
      const i = vecinas.indexOf(seccion);
      const vecina = vecinas[i + sentido];
      // No hay vecina por ese lado —la sección es la primera o la última de su
      // modo—: se suelta la rueda y la página vuelve a ser del visitante.
      if (i < 0 || !vecina) {
        mirador?.disable();
        return;
      }
      echarCerrojo();
      gsap.to(window, {
        scrollTo: { y: paradaDe(vecina), autoKill: false },
        duration: VIAJE,
        ease: 'power1.inOut',
      });
    }

    function avanzar(sentido: number) {
      // CADA ESCUCHA COMPRUEBA QUE LE TOCA. Hay un `Observer` por sección y
      // todos oyen la misma rueda, así que sin esta guarda un mismo gesto lo
      // atienden dos: medido, el primer gesto desde la portada disparaba el
      // paso del carril Y el salto de la portada, y el segundo pisaba el
      // destino del primero.
      if (!enRango()) return;
      if (sordo()) return;
      const destino = indice + sentido;
      if (destino < 0 || destino >= paneles) {
        salir(sentido);
        return;
      }
      irA(destino);
    }

    // Y NO SE ENCIENDE POR UN `isActive` PREMATURO. Recién construido, antes de
    // su primer refresco, el trigger puede decir que está activo aunque la
    // página esté arriba del todo: eso dejaba al carrusel escuchando desde el
    // primer píxel de la portada. Se comprueba contra la posición real.
    /* LA ESCUCHA SE ENCIENDE POR POSICIÓN, CON MARGEN, y no por `isActive`.
     *
     * Al aterrizar en la primera pieza la página queda en EXACTAMENTE el
     * arranque del fijado, y ahí ScrollTrigger todavía no se considera activo:
     * el carril se quedaba mudo justo en la parada a la que acababa de llegar,
     * y de la portada no se pasaba. Dos píxeles de margen a cada lado bastan y
     * no alcanzan a solaparse con la sección vecina. */
    ScrollTrigger.create({
      start: () => st.start - MARGEN,
      end: () => st.end + MARGEN,
      onToggle: (self) => (self.isActive ? tomar(st.progress) : mirador?.disable()),
    });
    if (enRango()) tomar(st.progress);

    alSoltar(() => mirador?.kill());
  });
}

/**
 * `[data-parada].canuto` — EL PASO BLOQUEADO DE UNA SECCIÓN DE UNA PANTALLA.
 *
 * Las portadas caben en una pantalla, así que no hay nada que leer dentro de
 * ellas desplazándose: un gesto significa «llévame a la siguiente». Aquí eso se
 * cumple literalmente, con el mismo viaje y el mismo cerrojo que usa el
 * carrusel.
 *
 * ES LO QUE QUITA EL DESFASE AL ENTRAR AL CATÁLOGO. Antes esta frontera la
 * gobernaba el aterrizaje general de `paradas`, que es de otra naturaleza:
 * deja que la página se desplace libre, espera a que el gesto muera y ENTONCES
 * corrige. Son dos movimientos, y el segundo llega tarde. Dentro del carrusel,
 * en cambio, el paso es inmediato y exacto. Al cruzar de un mecanismo al otro
 * se notaba el cambio de marcha.
 *
 * Las corridas —la obra, los servicios— se quedan fuera a propósito: ahí sí hay
 * varias pantallas que leer, y bloquear la rueda haría ilegible la sección.
 * Por eso la condición es `.canuto` y no `[data-parada]` a secas.
 */
function saltos(ctx: gsap.Context, root: ParentNode, alSoltar: Soltar) {
  const paradas_ = [...root.querySelectorAll<HTMLElement>('[data-parada]')];

  paradas_.forEach((seccion, i) => {
    // Solo secciones de una pantalla, y solo las que no tienen ya su propia
    // mecánica: el carrusel lleva la suya y el curado gobierna su barrido.
    if (!seccion.classList.contains('canuto')) return;
    if (seccion.hasAttribute('data-horizontal')) return;
    if (seccion.hasAttribute('data-curado') || seccion.hasAttribute('data-cierre')) return;

    let sordoHasta = 0;
    let mirador: Observer | undefined;
    const CERCA = 40;

    /* UN PASO SOLO SE BLOQUEA SI LA SECCIÓN CABE. Se comprueba cada vez, no una
     * vez al montar.
     *
     * Secuestrar la rueda en una sección más alta que la ventana deja al
     * visitante encerrado: no puede llegar al fondo de lo que está leyendo. En
     * el calificador eso sería atraparlo dentro del embudo, que es el peor
     * sitio del sitio para un fallo así.
     *
     * Y no es hipotético ni raro: medido en Chromium, el calificador de obra
     * mide 0,87 pantallas a 1440×900 —cabe— y 1,04 a 1280×720 —no cabe—. La
     * misma sección, dos comportamientos, y ninguna media query los distingue
     * porque lo que cambia no es el ancho.
     *
     * Cuando no cabe, la sección no pierde nada: se lee libre y sigue siendo
     * una parada del aterrizaje general.
     *
     * `offsetHeight` Y NO `scrollHeight`: lo que importa es la CAJA de la
     * sección, no lo que se salga de ella. Con `scrollHeight` el calificador
     * medía 851 px cuando en realidad ocupa 747: los 104 de diferencia eran la
     * fotografía de fondo desbordando su contenedor. Una imagen decorativa
     * decidiendo si se le quita la rueda al visitante. */
    const cabe = () => seccion.offsetHeight <= window.innerHeight + 8;

    const saltar = (sentido: number) => {
      // La misma guarda que en el carril, y por el mismo motivo: la ventana de
      // la escucha puede quedar abierta un instante de más mientras se viaja.
      if (Math.abs(window.scrollY - paradaDe(seccion)) > CERCA) return;
      if (performance.now() < sordoHasta) return;
      const vecina = paradas_[i + sentido];
      // Sin vecina por ese lado se suelta la rueda: el visitante está en el
      // extremo de su modo y la página vuelve a ser suya.
      if (!vecina) {
        mirador?.disable();
        return;
      }
      sordoHasta = performance.now() + (VIAJE + RESPIRO) * 1000;
      gsap.to(window, {
        scrollTo: { y: paradaDe(vecina), autoKill: false },
        duration: VIAJE,
        ease: 'power1.inOut',
      });
    };

    mirador = Observer.create({
      target: window,
      type: 'wheel,touch',
      preventDefault: true,
      tolerance: 12,
      enabled: false,
      onDown: () => saltar(1),
      onUp: () => saltar(-1),
    });

    /* La escucha solo se enciende CUANDO LA SECCIÓN ESTÁ EN REPOSO, no mientras
     * ocupa la pantalla. Es una ventana estrecha alrededor de su punto de
     * aterrizaje, y esa estrechez es deliberada: mientras se viaja hacia otra
     * sección no debe haber nadie escuchando, o el mismo gesto que ya se
     * atendió volvería a contarse al pasar por delante de esta. */
    ScrollTrigger.create({
      // SIN RECORTAR EN CERO. La portada aterriza en 0, así que con
      // `Math.max(0, ...)` su ventana quedaba en [0, 40] y el reposo caía justo
      // en el borde: ahí ScrollTrigger todavía no la da por activa y la escucha
      // no se encendía. Medido: bajando al formulario y volviendo, el tercer
      // gesto se perdía. Un arranque negativo es válido —solo significa «antes
      // del principio»— y deja el reposo dentro de la ventana.
      start: () => paradaDe(seccion) - CERCA,
      end: () => paradaDe(seccion) + CERCA,
      onToggle: (self) =>
        self.isActive && cabe() ? mirador?.enable() : mirador?.disable(),
    });

    /* EL VELO: la sección se enciende al llegar a su parada y se apaga al
     * dejarla.
     *
     * Es el mismo principio que el cruce entre piezas del catálogo —la
     * opacidad depende de LO LEJOS que está la sección de su punto de reposo, y
     * como se aleja hacia donde el gesto la empuja, el efecto sale solo—, y la
     * misma curva al cuadrado, por la misma razón: lineal, dos secciones a
     * medio camino quedarían las dos al 50 % y la pantalla se apagaría entera
     * un instante.
     *
     * La distancia se mide en pantallas para que un salto grande y uno pequeño
     * se apaguen al mismo ritmo. */
    const suya = () => paradaDe(seccion);

    /* LA ZONA MUERTA, y sin ella el velo se nota como un defecto.
     *
     * Las secciones no miden exactamente una pantalla: la portada mide 828 px
     * en una ventana de 900, así que estando en ella asoman 72 px de la
     * siguiente por debajo del pliegue. Con el apagado empezando en el mismo
     * punto de reposo, esa franja salía al 19 % de opacidad — una banda
     * oscurecida al pie de la pantalla que no se lee como una transición sino
     * como un fallo de pintado.
     *
     * Un cuarto de pantalla de holgura antes de empezar a apagar: lo que asoma
     * de la vecina se ve entero y con su color, y el velo solo entra en juego
     * cuando la sección se está yendo de verdad. */
    const HOLGURA = 0.25;
    const velar = () => {
      const d = Math.abs(window.scrollY - suya()) / window.innerHeight;
      const fuera = Math.max(0, d - HOLGURA) / (1 - HOLGURA);
      gsap.set(seccion, { opacity: Math.max(0, 1 - fuera * fuera) });
    };
    ScrollTrigger.create({
      start: () => suya() - window.innerHeight,
      end: () => suya() + window.innerHeight,
      onUpdate: velar,
      onRefresh: velar,
    });

    alSoltar(() => {
      mirador?.kill();
      // El velo escribe opacidad en línea: si no se retira, al desmontar el
      // movimiento —cruce de modos, cambio de punto de ruptura— la sección se
      // quedaría con el último valor que le tocó, que puede ser 0.
      gsap.set(seccion, { clearProps: 'opacity' });
    });
  });
}

/**
 * `data-parada` en el MODO CONSTRUIR — el relevo por opacidad.
 *
 * Construir se lee libre: no hay columna de paradas ni pasos bloqueados, el
 * scroll es del visitante de principio a fin. Lo que marca el paso de una
 * sección a otra no es entonces un aterrizaje sino un relevo: la que llega se
 * enciende y la que se va se apaga.
 *
 * POR QUÉ NO ES EL MISMO VELO QUE EL DE `saltos`. Aquel mide la distancia al
 * punto de reposo de la sección, y eso solo significa algo si hay reposos. Sin
 * paradas, una corrida de tres pantallas —la obra— estaría apagada casi entera
 * mientras se lee, porque su reposo queda lejísimos. Aquí se mide LO QUE LA
 * SECCIÓN OCUPA DE LA VENTANA, que vale igual para un canuto que para una
 * corrida: entra por el pie, se enciende, se recorre entera a plena luz y se
 * apaga cuando su borde inferior se va por arriba.
 *
 * El fundido se reparte a lo largo de un margen —un tercio de pantalla— y no
 * en el borde: apagar justo al cruzarlo se lee como un parpadeo.
 */
function velos(ctx: gsap.Context, root: ParentNode, alSoltar: Soltar) {
  const secciones = [...root.querySelectorAll<HTMLElement>('[data-parada]')];
  if (!secciones.length) return;

  /* El margen del fundido, en fracción de ventana. Un tercio: bastante para
   * que el cambio se vea suceder, poco para que ninguna sección pase mucho
   * rato a media luz — dos secciones tenues a la vez apagan la pantalla. */
  const MARGEN = 1 / 3;

  const recorte = (v: number) => Math.min(1, Math.max(0, v));

  /* LA CURVA, y no es lineal por una razón medible: en el relevo entre dos
   * secciones las dos pasan por el medio a la vez. Lineal, ambas quedan al
   * 50 % y la pantalla entera se apaga un instante — el mismo defecto que ya
   * corrigieron el velo de `saltos` y el cruce del catálogo.
   *
   * Smoothstep en vez del cuadrado que usan esos dos: aquí el fundido es
   * simétrico —entra y sale por el mismo margen—, y `a*a` solo suaviza un
   * extremo, dejando el otro con un corte. Esta pega suave en los dos y cruza
   * el medio rápido, que es justo lo que acorta el cruce a media luz. */
  const curva = (avance: number) => avance * avance * (3 - 2 * avance);

  secciones.forEach((seccion) => {
    const velar = () => {
      const caja = seccion.getBoundingClientRect();
      const alto = window.innerHeight;
      const margen = alto * MARGEN;
      // Cuánto le falta a la sección para estar dentro por cada lado: por el
      // pie mientras su techo sube, por el techo mientras su pie se va.
      const entra = recorte((alto - caja.top) / margen);
      const sale = recorte(caja.bottom / margen);
      gsap.set(seccion, { opacity: curva(Math.min(entra, sale)) });
    };

    ScrollTrigger.create({
      trigger: seccion,
      // Con el margen a cada lado: fuera de esta ventana la sección no se ve
      // ni de refilón y no hay nada que calcular.
      start: 'top bottom',
      end: 'bottom top',
      onUpdate: velar,
      onRefresh: velar,
    });

    // La opacidad se escribe en línea: si no se retira, al desmontar el
    // movimiento —cruce de modos, cambio de punto de ruptura— la sección se
    // quedaría con el último valor que le tocó, que puede ser 0.
    alSoltar(() => gsap.set(seccion, { clearProps: 'opacity' }));
  });
}

/**
 * `data-parada` — LA COLUMNA DE PARADAS.
 *
 * Cada sección de la página es una parada del scroll: se baja de una a la
 * siguiente y el desplazamiento aterriza en ella. Es el esqueleto del
 * recorrido, y lo gobierna GSAP y no el `scroll-snap` del navegador por dos
 * razones que aquí pesan:
 *
 *   - El navegador solo sabe aterrizar en los bordes de un elemento. Una
 *     sección fijada con `pin` no tiene un borde que signifique nada: su
 *     recorrido real es el `+=260%` que declara su trigger, no su alto. GSAP
 *     conoce esa geometría porque es quien la crea.
 *   - Y así las paradas se RECALCULAN en cada refresco. Este sitio desprende
 *     medio documento del DOM al cruzar de modo y rearma el movimiento entero
 *     (ver Base.astro); un array de posiciones escrito una vez quedaría
 *     apuntando a una página que ya no existe.
 *
 * ZONAS LIBRES. Las secciones fijadas con `scrub` —el curado, el cierre del
 * guadual— quedan fuera: dentro de ellas el scroll ES la línea de tiempo de una
 * animación, y aterrizar a mitad de un barrido lo convierte en saltos. Cada una
 * gobierna su propio reposo (ver `curado`). Entrar y salir de ellas sí son
 * paradas, porque son bordes de sección como cualquier otro.
 */
function paradas(ctx: gsap.Context, root: ParentNode) {
  const secciones = [...root.querySelectorAll<HTMLElement>('[data-parada]')];
  if (secciones.length < 2) return;

  let puntos: number[] = [];
  let libres: [number, number][] = [];

  // Se rehace en cada refresco, que es cuando GSAP ya ha colocado los
  // `pin-spacer` y las alturas son las definitivas. Calcularlo antes da las
  // posiciones de una página que todavía no existe.
  const medir = () => {
    const max = ScrollTrigger.maxScroll(window);
    if (!max) return;
    const fijados = ScrollTrigger.getAll().filter((t) => t.pin && t.vars.scrub);

    // UNA SOLA FUENTE DE VERDAD para dónde aterriza cada sección: `paradaDe`.
    // Tiene que ser la misma que usan los pasos bloqueados, o cada paso
    // terminaría en un punto que la columna querría corregir a continuación y
    // se verían dos movimientos encadenados.
    puntos = secciones
      .map((s) => paradaDe(s) / max)
      .map((p) => Math.min(Math.max(p, 0), 1));

    // El recorrido de cada sección fijada, en el mismo espacio normalizado.
    libres = fijados.map((t) => [t.start / max, t.end / max] as [number, number]);
  };

  ScrollTrigger.create({
    trigger: document.documentElement,
    start: 0,
    end: 'max',
    // EL ÚLTIMO EN MEDIR. En ScrollTrigger el número MENOR se refresca ANTES
    // —está al revés de lo que sugiere la palabra «prioridad»—, así que para
    // ir el último hay que pedir el número más alto, no el más bajo. Con un
    // -1 esta columna se medía la PRIMERA, antes de que el curado y el cierre
    // insertaran sus `pin-spacer`, y cada parada quedaba en la posición que su
    // sección ocupaba en un documento casi seis pantallas más corto.
    refreshPriority: 1000,
    onRefresh: medir,
    snap: {
      snapTo: (valor, self) => {
        if (!puntos.length) return valor;
        // Dentro de una sección fijada no se toca nada: manda ella.
        // El margen es para que el borde de entrada siga siendo una parada.
        for (const [a, b] of libres) if (valor > a + 0.005 && valor < b) return valor;

        // HACIA DONDE VA EL GESTO, NO HACIA DONDE ESTÁ MÁS CERCA.
        //
        // Aterrizar siempre en la parada más próxima tiene un efecto que en
        // papel no se ve y en la mano es intolerable: al empezar a bajar desde
        // una portada, un gesto normal deja el scroll sobre los 300 px, la
        // parada de arriba sigue siendo la más cercana, y la página TE DEVUELVE
        // al sitio del que acabas de salir. Medido en Chromium: soltar en 400
        // reposaba en 0.
        //
        // Bajando se aterriza en la siguiente y subiendo en la anterior. Un
        // gesto, un avance, y nunca un rebote hacia atrás.
        // SI YA ESTÁS EN UNA PARADA, NO HAY NADA QUE ACOMODAR.
        //
        // Parece una obviedad y es lo que faltaba: como el aterrizaje solo mira
        // hacia adelante, estando quieto en una parada elegía la SIGUIENTE. Con
        // el refresco que ScrollTrigger dispara al terminar de montarse, eso se
        // convertía en un salto solo, sin que nadie tocara la rueda: medido en
        // el modo construir, la página cargaba y se iba de la portada al
        // calificador ella sola. En compra no pasaba porque allí la parada
        // siguiente cae a 897 px, fuera del alcance de un gesto.
        const yaPuesto = 2 / ScrollTrigger.maxScroll(window);
        if (puntos.some((p) => Math.abs(p - valor) < yaPuesto)) return valor;

        const haciaAbajo = (self?.direction ?? 1) > 0;
        const candidatas = puntos.filter((p) =>
          haciaAbajo ? p > valor + 0.0005 : p < valor - 0.0005,
        );
        if (!candidatas.length) return valor;
        const cerca = candidatas.reduce((mejor, p) =>
          Math.abs(p - valor) < Math.abs(mejor - valor) ? p : mejor,
        );

        // EL ALCANCE, y es lo que hace que esto se pueda usar. Sin él, soltar
        // en mitad de la obra —que mide tres pantallas— te lanza una pantalla
        // entera hasta el borde más próximo, y leer una sección larga se
        // vuelve una pelea contra la página.
        //
        // Media pantalla: el aterrizaje solo actúa cuando el visitante ya
        // estaba llegando a una parada. Más allá, la sección se recorre libre,
        // que es lo que una lista de veinticinco fotografías necesita.
        //
        // Es la misma idea que el `proximity` del scroll-snap del navegador,
        // pero con el umbral escrito por nosotros en vez de decidido por cada
        // motor —y aplicado sobre una geometría que incluye los `pin-spacer`,
        // que es lo que el navegador no sabe ver.
        // Ahora que solo se mira hacia adelante, el alcance tiene que cubrir
        // un gesto entero: con media pantalla, salir de una portada de 0,92
        // pantallas se quedaba fuera de rango y no pasaba nada. Con 0,95 la
        // sección siguiente siempre está al alcance de un golpe decidido, y en
        // mitad de una corrida larga —donde la siguiente parada está a más de
        // una pantalla— se sigue leyendo libre, que es lo que se quiere.
        const alcance = (window.innerHeight * 0.95) / ScrollTrigger.maxScroll(window);
        return Math.abs(cerca - valor) < alcance ? cerca : valor;
      },
      // EL ACOMODO TIENE QUE SER UN ASENTAMIENTO, NO UN TIRÓN.
      //
      // Tres cosas lo deciden, y la duración es solo una:
      //
      // 1. LA ESPERA. Es lo que más se nota. El trackpad no suelta de golpe:
      //    entrega una cola de eventos que se va apagando, y si el aterrizaje
      //    arranca dentro de esa cola el usuario siente que la página le
      //    quita el gesto de las manos. Estaba en 0,10 s, que cae dentro de
      //    la cola; 0,18 espera a que el desplazamiento haya parado de verdad,
      //    y entonces el movimiento se lee como una respuesta y no como un
      //    forcejeo.
      //
      // 2. LA CURVA. `power2.inOut` arranca de cero y resuelve el medio muy
      //    rápido: con los 897 px que hay de la portada al catálogo, ese medio
      //    es un barrido. `power1.inOut` es la misma forma con mucha menos
      //    aceleración —entra, viaja parejo y se posa—, que es lo que se
      //    quiere de un acomodo.
      //
      // 3. LA DURACIÓN, y el que importa es el MÍNIMO. El máximo evita que un
      //    salto largo se haga eterno; el mínimo evita que una corrección
      //    corta se resuelva de un golpe seco. Estaba en 0,2 s: a esa
      //    velocidad, ajustar cien píxeles es un chasquido. Con 0,5 hasta el
      //    ajuste más pequeño se ve moverse.
      duration: { min: 0.5, max: 1.1 },
      delay: 0.18,
      ease: 'power1.inOut',
      // Sin predecir por velocidad y sin dirección obligada: se aterriza en la
      // parada más cercana a donde el visitante soltó, no en la que su gesto
      // insinuaba. Con secciones de altos muy distintos, predecir se salta una.
      inertia: false,
      directional: false,
    },
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

  // DÓNDE DESCANSA CADA ETAPA, en progreso del ScrollTrigger (0 a 1).
  //
  // Es el único snap de GSAP del sitio, y existe porque este contenido es
  // DISCRETO —cuatro etapas— y hoy se recorre como si fuera continuo. No
  // inventa una estructura: revela la que ya está en la línea de tiempo.
  //
  // Los números salen de esa línea de tiempo, no del ojo. La timeline dura 4.0
  // (el fundido verde→curada arranca en INICIO=0.4 y dura `largo - INICIO*2`
  // = 3.6). La etapa `i` termina de entrar en `INICIO + i*TRAMO + CAMBIO` y
  // empieza a salir en `INICIO + (i+1)*TRAMO - CAMBIO`, así que su ventana de
  // reposo —el tramo en el que se lee sola y quieta— es:
  //
  //     etapa 01   0.18 – 0.27      centro 0.225
  //     etapa 02   0.43 – 0.52      centro 0.475
  //     etapa 03   0.68 – 0.77      centro 0.725
  //     etapa 04   0.93 – 1.00      centro 0.965
  //
  // El 0 y el 1 son la salida: sin ellos el snap pelea con quien quiere
  // abandonar la sección por arriba o por abajo, que con un pin de 260% es
  // exactamente cuando peor se siente.
  const REPOSOS = [0, 0.225, 0.475, 0.725, 1];

  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: seccion,
      start: 'top top',
      // Cuatro etapas al mismo precio que un panel del catálogo. Estuvo en
      // `+=260%`, que salía de probar hasta que se veía bien y dejaba la
      // sección a 0,65 pantallas por etapa: cerca, pero distinto, y la página
      // cambiaba de marcha al entrar aquí. Ver `PASO`.
      end: () => '+=' + pasos.length * paso(),
      pin: true,
      scrub: 1,
      anticipatePin: 1,
      invalidateOnRefresh: true,
      snap: {
        /* HACIA DONDE VA EL GESTO, igual que la columna de paradas, y aquí
         * no es un refinamiento: es lo que permite entrar y salir.
         *
         * Al reposo más cercano, el `0` de la lista es una trampa. El pin
         * mide 2,8 pantallas, así que el punto medio entre el `0` y la
         * etapa 01 cae en 0,1125 — 283 px a 900 de alto. Aterrizando en el
         * arranque de la sección —que es donde deja `paradas`, y donde deja
         * la salida del catálogo— cualquier gesto más corto que eso tenía el
         * `0` más cerca y la sección lo devolvía al sitio. Y `scrub: 1` lo
         * empeora: el progreso que el snap juzga va por detrás del scroll
         * real, así que la cuenta sale aún más corta. El visitante empuja y
         * no pasa nada.
         *
         * Mirando solo hacia adelante, un gesto hacia abajo desde el arranque
         * solo puede ir a la etapa 01. Y en los extremos —bajando desde el 1,
         * subiendo desde el 0— no queda candidata: se devuelve el valor tal
         * cual y la sección suelta al visitante, que es como se sale de aquí. */
        snapTo: (valor, self) => {
          const haciaAbajo = (self?.direction ?? 1) > 0;
          const candidatas = REPOSOS.filter((p) =>
            haciaAbajo ? p > valor + 0.001 : p < valor - 0.001,
          );
          if (!candidatas.length) return valor;
          return candidatas.reduce((mejor, p) =>
            Math.abs(p - valor) < Math.abs(mejor - valor) ? p : mejor,
          );
        },
        // MÁS CORTO QUE EL `scrub`, y esa es la regla. El scrub de esta
        // sección es 1, así que la página ya viene arrastrando un segundo de
        // retraso sobre el gesto; si el aterrizaje durase lo mismo o más, lo
        // que se ve después de soltar es la página siguiendo sola, y eso se
        // lee como que no respondió. El mínimo es para el ajuste corto —te
        // pasaste treinta píxeles del reposo— y el máximo para el salto entre
        // etapas contiguas, que es un cuarto del recorrido fijado.
        duration: { min: 0.15, max: 0.45 },
        // El trackpad no suelta de golpe: entrega una cola de eventos que se
        // van apagando. Sin esta espera el snap dispara en la primera
        // micro-pausa de esa cola y tira de la página mientras el dedo todavía
        // va bajando. 80 ms es lo que tarda la inercia en dejar de parecer
        // gesto y empezar a parecer reposo.
        delay: 0.08,
        ease: 'power1.inOut',
        // NO PREDECIR POR VELOCIDAD. Con inercia, ScrollTrigger elige el
        // reposo al que el gesto *iba* a llegar, y un golpe de rueda decidido
        // se salta una etapa entera —que es justo lo que este snap venía a
        // evitar: el contenido es discreto y ninguna de las cuatro etapas es
        // prescindible—. Sin ella aterriza en el reposo más cercano al punto
        // donde el usuario realmente soltó.
        inertia: false,
        // Y por lo mismo, sin dirección: si alguien se pasa un poco del
        // reposo, `directional` lo obligaría a seguir hasta el siguiente en
        // vez de devolverlo al que tenía delante.
        directional: false,
      },
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
      /* TRES PASOS, EN LA UNIDAD DEL SITIO. Estuvo en `+=300%`, un número
       * suelto que no se correspondía con nada: tres pantallas enteras de
       * barrido decorativo DEBAJO del botón de WhatsApp, y el bloque más
       * grande de los dos modos.
       *
       * En pasos son 2,1 pantallas —el mismo precio por momento que una pieza
       * del catálogo o una etapa del curado—, así que la página deja de
       * cambiar de marcha al llegar aquí y se ahorra casi una pantalla en cada
       * modo. El barrido no pierde nada: 72 fotogramas repartidos en 2,1
       * pantallas siguen sobrando para que se lea continuo.
       *
       * Tres y no cuatro porque esto va después de la conversión: es un
       * epílogo, y un epílogo no puede costar más que cualquiera de las
       * secciones que llevan a ella. */
      end: () => '+=' + 3 * paso(),
      pin: escena,
      invalidateOnRefresh: true,
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
    // La leyenda ya no acompaña todo el descenso: solo lo presenta. A partir
    // del primer mensaje sobraba —dos rótulos a la vez sobre la misma imagen—
    // y encima decía en pequeño lo que el mensaje dice en grande.
    .to(leyenda, { opacity: 1, duration: 0.1 }, 0.2)
    .to(leyenda, { opacity: 0, duration: 0.1 }, 0.34);

  /* LOS TRES MENSAJES, uno por plano de la secuencia.
   *
   * El reparto vive aquí y no en el componente porque es una cuestión de
   * recorrido, no de contenido: `abierto` —lo que ya se ha reproducido— va de
   * 0 en el dosel a 1 en el brote, y cada mensaje tiene que entrar cuando la
   * cámara está en su plano. Con los tres a intervalos iguales el del rizoma
   * llegaba con la secuencia ya parada en el último fotograma.
   *
   * Cada uno entra, se queda quieto mientras la imagen sigue bajando y sale
   * antes de que llegue el siguiente: los solapes se leen como un cambio de
   * idea a media frase.
   *
   * El dibujo se talla DENTRO de la línea de tiempo, escribiendo `--gu-t` en
   * cada gubia —el avance del filo, de 0 a 1—. Estuvo como animación CSS
   * disparada por una clase, que es como se talla en el resto del sitio, y
   * aquí no vale: con `scrub` la rueda lleva el tramo hacia delante y hacia
   * atrás, y una animación CSS no se entera. Medido: el dibujo se quedaba con
   * un trazo entero y doce en `scaleX(0)`, según dónde parase la rueda.
   * Ver la nota del componente.
   */
  const momentos = Array.from(cierre.querySelectorAll<HTMLElement>('[data-momento]'));
  // Dónde entra cada uno dentro del tramo, y cuánto se queda. El primero
  // espera a que el guadual esté abierto del todo (0,3) y el último sale antes
  // del final, para que el tramo cierre con la imagen sola.
  const VENTANAS: [number, number][] = [
    [0.36, 0.54],
    [0.58, 0.74],
    [0.78, 0.94],
  ];

  momentos.forEach((m, i) => {
    const [entra, sale] = VENTANAS[i] ?? VENTANAS[VENTANAS.length - 1];
    const gubias = m.querySelectorAll('.gu');

    tl.fromTo(m, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.06, ease: 'power2.out' }, entra)
      // El filo entra trazo a trazo mientras el bloque sube. Empieza con el
      // bloque ya en marcha —un pelo después— para que primero llegue la
      // pieza y luego se talle, y no las dos cosas a la vez.
      .fromTo(
        gubias,
        { '--gu-t': 0 },
        { '--gu-t': 1, duration: 0.05, ease: 'power2.out', stagger: 0.0015 },
        entra + 0.01,
      )
      .to(m, { opacity: 0, y: -20, duration: 0.05, ease: 'power2.in' }, sale);
  });
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

/**
 * LA UNIDAD DE RECORRIDO DEL SITIO: lo que cuesta pasar de un momento al
 * siguiente, en pantallas.
 *
 * Todo lo que se recorre por pasos —los paneles de una sección horizontal, las
 * etapas del curado— avanza con este mismo precio. Antes cada sección se
 * inventaba el suyo: el catálogo iba a 0,80 pantallas por pieza y el curado a
 * 0,65, y aunque ninguna de las dos está mal por separado, juntas hacen que la
 * página cambie de marcha sin motivo. Con una sola unidad, un gesto de rueda
 * recorre lo mismo esté donde esté.
 *
 * 0,7 y no 1: a una pantalla completa por paso el recorrido se siente pesado
 * —hay que empujar de más para ver algo—, y por debajo de 0,5 un solo golpe de
 * trackpad se salta dos paradas. Medido en Chromium a 1440×900: con 0,7 el
 * catálogo entero son 2,8 pantallas para cinco piezas.
 */
const PASO = 0.7;

/** Lo que mide un paso ahora mismo, en píxeles. */
const paso = () => window.innerHeight * PASO;

/* CUÁNTO DURA UN SALTO GOBERNADO Y CUÁNTO DURA LA SORDERA.
   Compartidos por el carrusel y por las secciones de una pantalla: los dos
   tienen que sentirse el mismo gesto, o al pasar de uno a otro se nota el
   cambio de mecanismo —que es justo lo que se estaba notando entre la portada
   de compra y el catálogo—. */
const VIAJE = 0.7;
const RESPIRO = 0.18;

/** Dónde aterriza una sección. Es la misma cuenta que usa `paradas`, y tiene
 *  que serlo: si un salto dejara la página en un punto distinto del que calcula
 *  el aterrizaje general, este se dispararía a continuación para corregirlo y
 *  se verían dos movimientos. Una sección fijada aterriza en el arranque de su
 *  pin; el resto, en su techo menos la barra de navegación. */
function paradaDe(el: HTMLElement) {
  const suyo = ScrollTrigger.getAll().find(
    (t) => t.pin && t.vars.scrub && (t.trigger === el || t.pin === el),
  );
  if (suyo) return suyo.start;

  const nav =
    parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue('--alto-nav'),
    ) * 16 || 88;

  /* EL AIRE PARA LA BARRA SALE DEL HUECO QUE LA SECCIÓN DEJA, NO DE SU
   * CONTENIDO.
   *
   * Descontar el alto del nav a secas es correcto mientras a la sección le
   * sobre pantalla: así su rótulo no queda debajo de la barra. Pero una sección
   * que OCUPA la ventana entera no tiene hueco de donde sacarlo, y el descuento
   * se lo come ella: aterriza 88 px antes de su techo, con la sección anterior
   * todavía asomando por arriba y su propio pie cortado por abajo.
   *
   * Medido: el calificador de obra mide 900 px en una ventana de 900 y
   * aterrizaba en 809 en vez de 897 — la portada seguía ocupando el 10 % de la
   * pantalla y el formulario se veía al 90 %. Un paso que deja dos secciones a
   * la vista no es un paso.
   *
   * Con el mínimo entre las dos cantidades, la portada —que mide 828 y deja 72
   * de hueco— sigue aterrizando en 0, y el formulario, que no deja ninguno,
   * aterriza clavado en su techo. */
  const caja = el.getBoundingClientRect();
  const hueco = Math.max(0, window.innerHeight - caja.height);
  return Math.max(0, caja.top + window.scrollY - Math.min(nav, hueco));
}

/**
 * QUÉ MODO ESTÁ EN PANTALLA, o `null` si esto no es la portada.
 *
 * Se lee del bloque, no del `html`: el modo inactivo se DESPRENDE del DOM (ver
 * Base.astro), así que el bloque presente es la verdad más directa que hay, y
 * no depende de que `data-modo` se haya repuesto ya después de una navegación.
 * En una ficha de obra no hay bloques y devuelve `null` — allí no hay modos y
 * el recorrido es el de siempre.
 */
function modoEnPantalla(root: ParentNode): string | null {
  const bloque =
    root.querySelector<HTMLElement>('[data-modo]') ??
    document.querySelector<HTMLElement>('#contenido > [data-modo]');
  return bloque?.dataset.modo ?? null;
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
      // Un segundo escalón, por encima del de los pines. El carril horizontal
      // del catálogo existe en las dos formas: por debajo de 900 px es un
      // contenedor con scroll y `scroll-snap` de CSS —gesto táctil nativo— y
      // por encima es esta sección fijada. Con un solo umbral las dos se
      // pisarían en la franja de en medio.
      ancho: '(min-width: 901px)',
    },
    (contexto) => {
      const { conMovimiento, escritorio, ancho } = contexto.conditions!;

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
      /* CADA MODO SE RECORRE COMO PIDE SU CONTENIDO.
       *
       * COMPRAR va por paradas: es un recorrido de venta —portada, catálogo,
       * curado, cierre— donde cada sección es una lámina que se mira entera, y
       * el catálogo horizontal necesita que se entre y se salga de él por su
       * borde.
       *
       * CONSTRUIR se lee libre. Ahí hay una corrida de veinticinco fotografías
       * de obra y una lista de servicios: contenido que se recorre a la
       * velocidad de quien lee, y al que el aterrizaje le quitaba el gesto de
       * las manos. El relevo entre secciones lo cuenta la opacidad (`velos`),
       * que no toca el scroll. */
      const modo = modoEnPantalla(root);
      const conParadas = modo !== 'construir';

      if (!conParadas) velos(contexto, root, alSoltar);

      if (escritorio) {
        curado(contexto, root);
        cierreGuadual(contexto, root, alSoltar);
        // Antes de las paradas: cada sección horizontal añade su propio
        // `pin-spacer` al documento, y la columna tiene que medir después.
        if (ancho) horizontal(contexto, root, alSoltar);

        // LAS PARADAS VAN LAS ÚLTIMAS, y no es opcional: miden la página ya
        // colocada, y el curado y el cierre añaden entre los dos casi seis
        // pantallas de recorrido con sus `pin-spacer`. Montadas antes, cada
        // parada quedaría en la posición que la sección ocupaba ANTES de que
        // los pines estiraran el documento.
        //
        // Solo en escritorio, como los pines: en celular robarle el
        // desplazamiento al dedo se siente como que la página se trabó, y ahí
        // el recorrido es una lectura continua.
        if (conParadas) {
          paradas(contexto, root);
          // Y los pasos bloqueados de las secciones de una pantalla, que se
          // apoyan en las mismas paradas que acaba de medir la columna.
          saltos(contexto, root, alSoltar);
        }
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
