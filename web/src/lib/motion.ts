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
 * Quien la dispara es `iniciarMovimiento`, y en la primera carga eso ocurre
 * cuando el velo empieza a abrirse (ver Base.astro y Splash.astro).
 */
function obertura(ctx: gsap.Context, root: ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-obertura]').forEach((cont) => {
    const pasos = Array.from(cont.querySelectorAll<HTMLElement>('[data-alza]'));
    if (!pasos.length) return;

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
 * `data-morfo` — congela la banda de verbos mientras no se la ve.
 *
 * El fundido de la banda lleva un filtro SVG y un desenfoque animado: mientras
 * corre, el navegador repinta esa caja en cada fotograma, esté o no en pantalla.
 * Aquí solo se conmuta una variable —el CSS la lee en `animation-play-state`—,
 * así que sin JavaScript la banda sigue animándose igual.
 */
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
function giratorioArrastre(ctx: gsap.Context, root: ParentNode, conMovimiento: boolean) {
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

    gsap.ticker.add((_t, dt) => {
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
    });

    let objetivo = 0;
    let xInicial = 0;
    let iInicial = 0;
    let ultimaX = 0;
    let ultimoT = 0;
    let porPixel = 0;

    lienzo.addEventListener('pointerdown', (e) => {
      arrastrando = true;
      inercia = 0;
      // Un recorrido entero por cada ancho y cuarto de arrastre; medido contra
      // el lienzo para que el gesto cueste lo mismo en un portátil que en un
      // celular. Se calcula al agarrar y no en cada movimiento: si la caja
      // cambiara de ancho a mitad del gesto, el modelo pegaría un tirón.
      porPixel = total / (lienzo.clientWidth * 1.25);
      objetivo = iInicial = indice;
      xInicial = ultimaX = e.clientX;
      ultimoT = e.timeStamp;
      lienzo.setPointerCapture(e.pointerId);
      e.preventDefault();
    });

    lienzo.addEventListener('pointermove', (e) => {
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
  });
}

/**
 * `data-giratorio` — el modelo gira sobre sí mismo, fotograma a fotograma.
 *
 * Solo gira mientras su vista está a la vista: fuera de ella el bucle se para
 * y deja de consumir cuadros.
 */
function giratorio(ctx: gsap.Context, root: ParentNode) {
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
function cierreGuadual(ctx: gsap.Context, root: ParentNode) {
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

export function iniciarMovimiento(root: ParentNode = document) {
  const mm = gsap.matchMedia();

  mm.add(
    {
      conMovimiento: '(prefers-reduced-motion: no-preference)',
      sinMovimiento: '(prefers-reduced-motion: reduce)',
      escritorio: '(min-width: 781px)',
    },
    (contexto) => {
      const { conMovimiento, escritorio } = contexto.conditions!;

      // Con movimiento reducido todo queda visible y quieto. Es una versión
      // legítima del sitio, no una degradada.
      if (!conMovimiento) {
        root.querySelectorAll<HTMLElement>(
          '[data-revelar-texto], [data-revelar-palabras]',
        ).forEach((el) => (el.style.visibility = 'visible'));
        gsap.set('[data-capa="curada"]', { opacity: 1 });
        gsap.set('[data-capa="verde"], [data-paso]', { clearProps: 'all' });
        // La obertura se salta entera, pero su estado inicial vive en el CSS:
        // hay que devolver la portada a la vista con estilo en línea.
        gsap.set('[data-alza]', { opacity: 1, y: 0, scale: 1 });
        // El arrastre no es adorno: es el único modo de ver el modelo por
        // detrás. Se mantiene, sin giro de cortesía ni inercia.
        giratorioArrastre(contexto, root, false);
        rotante(contexto, root, false);
        indiceObra(contexto, root, false);
        // El panel del calificador cruza igual, sin fundido: es la respuesta a
        // lo que el visitante está mirando.
        visorCalificador(contexto, root, false);
        return;
      }

      obertura(contexto, root);
      revelarTexto(contexto, root);
      revelarPalabras(contexto, root);
      entradas(contexto, root);
      descubrirImagenes(contexto, root);
      morfo(contexto, root);
      marcos(contexto, root);
      deriva(contexto, root);
      visorCalificador(contexto, root, true);
      giratorio(contexto, root);
      giratorioArrastre(contexto, root, true);
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
        cierreGuadual(contexto, root);
      }
      else {
        gsap.set('[data-capa="curada"]', { opacity: 1 });
        gsap.set('[data-capa="verde"]', { opacity: 0 });
      }
    },
  );

  // Las imágenes cambian el alto de la página al cargar; sin esto los
  // disparadores quedan calculados sobre posiciones viejas. Al rearmar tras una
  // navegación con ClientRouter el evento `load` ya pasó, así que se refresca
  // de una vez.
  if (document.readyState === 'complete') ScrollTrigger.refresh();
  else window.addEventListener('load', () => ScrollTrigger.refresh(), { once: true });

  return () => mm.revert();
}
