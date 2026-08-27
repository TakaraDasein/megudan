/**
 * Muro de obra — vendorizado de `DriftWall` (React Bits, variante JS + CSS).
 *
 * El cuerpo del componente se deja tal como viene de upstream, con nombres de
 * clase y variables en inglés, para poder seguir comparándolo contra
 * reactbits.dev cuando salga una versión nueva. Lo que es de Megudan va fuera:
 * el envoltorio `MuroProyectos.astro` y los estilos añadidos en el CSS, ambos
 * marcados.
 *
 * Cambios sobre el original, y por qué:
 *
 * 1. Los enlaces internos abren en la misma pestaña. El original pone siempre
 *    `target="_blank"`, que para `/obra/casa-anolaima` sería sacar al visitante
 *    de su propia sesión. Solo lo externo (http…) sigue abriendo aparte.
 * 2. Se rotula la ficha activa con el título del proyecto. Sin eso el muro es
 *    bonito pero mudo: no se sabe a qué obra lleva el clic.
 * 3. Sin `items` no se pinta nada, en vez de caer a las quince fotos de demo de
 *    picsum.photos — que además serían peticiones a un tercero.
 * 4. El clic entra a la obra por un túnel: el muro se abalanza sobre el
 *    visitante y le pasa de largo, como si la cámara se metiera por el hueco de
 *    la ficha que pulsó. Ver `iniciarSalto`.
 * 5. El bucle se cubre con más holgura. El original calcula las copias contra
 *    el alto del contenedor, pero el plano va escalado 1.18 y en perspectiva:
 *    ocupa bastante más que ese alto y el final de la columna llegaba a
 *    asomarse. Ver `columnMeta`.
 * 6. El ancho de ficha se ajusta al contenedor (`fit`) y el aumento del plano
 *    es un prop (`scale`) en vez del 1.18 fijo del original. Sin las dos cosas
 *    las columnas de los extremos se salen de la pantalla y el muro aparece
 *    cortado.
 */
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import './MuroProyectos.css';

/**
 * Lo que dura el túnel, en ms. El mismo número gobierna el velo en el CSS.
 *
 * Corto a propósito: un clic tiene que llevar a la obra de una vez, y por
 * encima de los ~400 ms la animación deja de leerse como respuesta al gesto y
 * empieza a leerse como espera.
 */
const SALTO_MS = 380;



const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const columnFactor = (index, variance) => {
  const pseudo = ((index * 0.6180339887 + 0.35) % 1) * 2 - 1;
  return 1 + variance * pseudo;
};

const esExterno = href => /^[a-z][a-z0-9+.-]*:/i.test(href ?? '');

const MuroProyectos = ({
  items = [],
  columns = 5,
  tileWidth = 200,
  tileHeight = 132,
  gap = 18,
  radius = 14,
  tilt = 16,
  turn = -14,
  roll = 0,
  perspective = 1200,
  depth = 120,
  speed = 42,
  direction = 'up',
  variance = 0.45,
  parallax = 0.6,
  scale = 1.18,
  /** Encoge la ficha lo justo para que las columnas quepan enteras. */
  fit = false,
  pauseOnHover = false,
  lift = 64,
  fade = 0.6,
  dim = 0.55,
  grayscale = false,
  overlayColor = '#060010',
  className = '',
  style
}) => {
  const containerRef = useRef(null);
  const planeRef = useRef(null);
  const trackRefs = useRef([]);
  const rafRef = useRef(null);

  const offsetsRef = useRef([]);
  const velocitiesRef = useRef([]);
  const hoveredColRef = useRef(-1);
  const wallHoveredRef = useRef(false);
  const pointerRef = useRef({ x: 0, y: 0 });
  const pointerDampedRef = useRef({ x: 0, y: 0 });
  const lastTsRef = useRef(null);

  const [containerHeight, setContainerHeight] = useState(600);
  const [containerWidth, setContainerWidth] = useState(1200);
  const [activeId, setActiveId] = useState(null);
  const activeIdRef = useRef(null);
  const [reduced, setReduced] = useState(false);
  const [salto, setSalto] = useState(false);
  const saltoRef = useRef(null);
  const buceandoRef = useRef(false);

  useEffect(() => {
    setReduced(prefersReducedMotion());
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = e => setReduced(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  // Cambio 6: el muro nunca es más ancho que su contenedor. Se reparte el
  // ancho disponible entre las columnas y la ficha guarda su proporción; el
  // `tileWidth` que llega por prop pasa a ser el máximo, no el valor fijo.
  const [tileW, tileH] = useMemo(() => {
    if (!fit) return [tileWidth, tileHeight];
    const disponible = Math.max(80, containerWidth / scale - gap);
    const w = Math.min(tileWidth, Math.floor(disponible / columns) - gap);
    return [w, Math.round(tileHeight * (w / tileWidth))];
  }, [fit, tileWidth, tileHeight, containerWidth, columns, gap, scale]);

  const columnItems = useMemo(() => {
    const cols = Array.from({ length: columns }, () => []);
    items.forEach((item, i) => cols[i % columns].push(item));
    return cols.map(col => (col.length ? col : items.slice(0, 1)));
  }, [items, columns]);

  const columnMeta = useMemo(() => {
    const unit = tileH + gap;
    return columnItems.map(col => {
      const copyHeight = Math.max(unit, col.length * unit);
      // El plano va escalado y en perspectiva: la columna se ve mucho más
      // larga que el contenedor. Con 1.6 el final llegaba a asomarse en las
      // columnas rápidas; 2.6 y dos copias de margen lo dejan continuo.
      const copies = Math.max(3, Math.ceil((containerHeight * 2.6) / copyHeight) + 2);
      return { copyHeight, copies };
    });
  }, [columnItems, tileH, gap, containerHeight]);

  useLayoutEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(([entry]) => {
      setContainerHeight(entry.contentRect.height || 600);
      setContainerWidth(entry.contentRect.width || 1200);
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const baseVelocities = useMemo(() => {
    const dirSign = direction === 'up' ? 1 : -1;
    return columnItems.map((_, c) => {
      const altSign = c % 2 === 0 ? 1 : -1;
      return speed * columnFactor(c, variance) * dirSign * altSign;
    });
  }, [columnItems, speed, direction, variance]);

  useEffect(() => {
    offsetsRef.current = columnMeta.map((meta, c) => meta.copyHeight * ((c * 0.37) % 1));
    velocitiesRef.current = columnItems.map(() => 0);
  }, [columnMeta, columnItems]);

  const applyPlaneTransform = useCallback(
    (px, py) => {
      const plane = planeRef.current;
      if (!plane) return;
      plane.style.transform =
        `translate(-50%, -50%) scale(${scale}) ` +
        `rotateX(${tilt + py}deg) rotateY(${turn + px}deg) rotateZ(${roll}deg) ` +
        `translateZ(${-depth}px)`;
    },
    [tilt, turn, roll, depth, scale]
  );

  useEffect(() => {
    const animate = ts => {
      // Durante el túnel el plano lo gobierna una transición de CSS y la deriva
      // se detiene: si las columnas siguen corriendo, el picado no se lee.
      if (buceandoRef.current) {
        rafRef.current = requestAnimationFrame(animate);
        return;
      }
      if (lastTsRef.current === null) lastTsRef.current = ts;
      const dt = Math.min(0.05, Math.max(0, ts - lastTsRef.current) / 1000);
      lastTsRef.current = ts;

      const maxTilt = parallax * 8;
      const targetX = pointerRef.current.x * maxTilt;
      const targetY = -pointerRef.current.y * maxTilt;
      const damp = 1 - Math.exp(-dt / 0.12);
      pointerDampedRef.current.x += (targetX - pointerDampedRef.current.x) * damp;
      pointerDampedRef.current.y += (targetY - pointerDampedRef.current.y) * damp;
      applyPlaneTransform(pointerDampedRef.current.x, pointerDampedRef.current.y);

      if (!reduced) {
        for (let c = 0; c < trackRefs.current.length; c++) {
          const meta = columnMeta[c];
          if (!meta) continue;
          const paused = wallHoveredRef.current && pauseOnHover;
          const factor = paused || hoveredColRef.current === c ? 0 : 1;
          const target = baseVelocities[c] * factor;

          const ease = 1 - Math.exp(-dt / (target === 0 ? 0.16 : 0.28));
          velocitiesRef.current[c] += (target - velocitiesRef.current[c]) * ease;
          let next = (offsetsRef.current[c] ?? 0) + velocitiesRef.current[c] * dt;
          next = ((next % meta.copyHeight) + meta.copyHeight) % meta.copyHeight;
          offsetsRef.current[c] = next;

          const el = trackRefs.current[c];
          if (el) el.style.transform = `translate3d(0, ${-next}px, 0)`;
        }
      } else {
        for (let c = 0; c < trackRefs.current.length; c++) {
          const el = trackRefs.current[c];
          const meta = columnMeta[c];
          if (el && meta) el.style.transform = `translate3d(0, ${-(offsetsRef.current[c] ?? 0)}px, 0)`;
        }
      }

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      lastTsRef.current = null;
    };
  }, [baseVelocities, columnMeta, pauseOnHover, parallax, reduced, applyPlaneTransform]);

  const activate = useCallback((id, index) => {
    activeIdRef.current = id;
    hoveredColRef.current = index;
    setActiveId(id);
  }, []);
  const release = useCallback(() => {
    activeIdRef.current = null;
    hoveredColRef.current = -1;
    setActiveId(null);
  }, []);

  const handlePointerMove = useCallback(
    e => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      if (parallax > 0 && !reduced) {
        pointerRef.current = {
          x: (e.clientX - rect.left) / rect.width - 0.5,
          y: (e.clientY - rect.top) / rect.height - 0.5
        };
      }
      const hit = document.elementFromPoint(e.clientX, e.clientY);
      const tile = hit && hit.closest ? hit.closest('[data-tile-id]') : null;
      if (!tile) return;
      const id = tile.dataset.tileId;
      if (id === activeIdRef.current) return;
      activeIdRef.current = id;
      hoveredColRef.current = Number(tile.dataset.col);
      setActiveId(id);
    },
    [parallax, reduced]
  );

  const handlePointerLeaveWall = useCallback(() => {
    wallHoveredRef.current = false;
    pointerRef.current = { x: 0, y: 0 };
    release();
  }, [release]);

  const cssVars = useMemo(
    () => ({
      '--dw-tile-w': `${tileW}px`,
      '--dw-tile-h': `${tileH}px`,
      '--dw-gap': `${gap}px`,
      '--dw-radius': `${radius}px`,
      '--dw-perspective': `${perspective}px`,
      '--dw-lift': `${lift}px`,
      '--dw-dim': dim,
      '--dw-gray': grayscale ? 1 : 0,
      '--dw-overlay': overlayColor,
      '--dw-edge': `${Math.max(0, (1 - fade) * 100)}%`,
      ...style
    }),
    [tileW, tileH, gap, radius, perspective, lift, dim, grayscale, overlayColor, fade, style]
  );

  /**
   * Cambio 4: un clic basta, y el paso a la obra se atraviesa.
   *
   * El punto de fuga se muda al centro de la ficha que se pulsó
   * (`perspective-origin`) y el plano avanza hasta pasar de largo al visitante:
   * las fichas se abren hacia los bordes y se deshacen contra la máscara del
   * propio muro, que ya desvanece los cantos. La aceleración va toda al final
   * —`cubic-bezier` de salida brusca—, que es lo que hace que se lea como
   * entrar y no como acercarse.
   *
   * Se anima el DOM y no la View Transition del ClientRouter a propósito: así
   * el efecto existe en cualquier navegador, tenga o no la API, y no depende de
   * cuándo decida el router hacer el intercambio.
   *
   * El velo va en un portal a `document.body`: `.drift-wall` tiene
   * `perspective`, que crea bloque contenedor, así que un `position: fixed`
   * dentro del muro quedaría atrapado y recortado por su máscara.
   */
  const iniciarSalto = useCallback(
    (e, item, tileEl) => {
      // Movimiento reducido, o el visitante que quiere abrir en otra pestaña:
      // se deja el enlace en paz.
      if (reduced || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
      const cont = containerRef.current;
      const plano = planeRef.current;
      if (!cont || !plano || saltoRef.current) return;

      e.preventDefault();

      const caja = cont.getBoundingClientRect();
      const r = tileEl.getBoundingClientRect();
      const ox = ((r.left + r.width / 2 - caja.left) / caja.width) * 100;
      const oy = ((r.top + r.height / 2 - caja.top) / caja.height) * 100;
      cont.style.perspectiveOrigin = `${ox}% ${oy}%`;

      buceandoRef.current = true;
      saltoRef.current = item.href;

      plano.style.transition = `transform ${SALTO_MS}ms cubic-bezier(0.5, 0, 0.85, 0.35)`;
      plano.style.transform =
        `translate(-50%, -50%) scale(${scale}) ` +
        `rotateX(${tilt}deg) rotateY(${turn}deg) rotateZ(${roll}deg) ` +
        `translateZ(${perspective * 0.82}px)`;

      setSalto(true);
    },
    [reduced, scale, tilt, turn, roll, perspective]
  );

  useEffect(() => {
    if (!salto) return;
    const t = setTimeout(async () => {
      const href = saltoRef.current;
      if (!href) return;
      try {
        const { navigate } = await import('astro:transitions/client');
        navigate(href);
      } catch {
        window.location.href = href;
      }
    }, SALTO_MS);
    return () => clearTimeout(t);
  }, [salto]);

  const renderTile = (item, id, colIndex) => {
    const inner = (
      <span className="drift-wall__inner">
        <img
          src={item.image}
          srcSet={item.srcset}
          sizes={`${tileW}px`}
          alt={item.alt ?? item.title ?? ''}
          loading="lazy"
          decoding="async"
          draggable={false}
        />
        <span className="drift-wall__overlay" aria-hidden="true" />
        {item.title && <span className="drift-wall__rotulo">{item.title}</span>}
      </span>
    );
    const commonProps = {
      className: `drift-wall__tile${activeId === id ? ' is-active' : ''}`,
      'data-tile-id': id,
      'data-col': colIndex,
      onFocus: () => activate(id, colIndex),
      onBlur: release
    };
    if (item.href) {
      // Cambio 1: solo lo externo sale a otra pestaña.
      const fuera = esExterno(item.href);
      return (
        <a
          key={id}
          href={item.href}
          target={fuera ? '_blank' : undefined}
          rel={fuera ? 'noreferrer noopener' : undefined}
          aria-label={item.title ? `Ver la obra: ${item.title}` : undefined}
          onClick={fuera ? undefined : (e) => iniciarSalto(e, item, e.currentTarget)}
          {...commonProps}
        >
          {inner}
        </a>
      );
    }
    return (
      <div key={id} tabIndex={0} role="button" aria-label={item.title ?? 'tile'} {...commonProps}>
        {inner}
      </div>
    );
  };

  const rootClass = ['drift-wall', reduced ? 'drift-wall--reduced' : '', className].filter(Boolean).join(' ');

  // Cambio 3: sin fichas no hay muro. Nunca las quince fotos de demo.
  if (!items.length) return null;

  const muro = (
    <div
      ref={containerRef}
      className={rootClass}
      style={cssVars}
      onPointerMove={handlePointerMove}
      onPointerEnter={() => {
        wallHoveredRef.current = true;
      }}
      onPointerLeave={handlePointerLeaveWall}
      role="group"
      aria-label="Muro de obra construida"
    >
      <div ref={planeRef} className="drift-wall__plane">
        {columnItems.map((col, c) => {
          const meta = columnMeta[c];
          const copies = Array.from({ length: meta.copies });
          return (
            <div className="drift-wall__col" key={`col-${c}`}>
              <div className="drift-wall__track" ref={el => (trackRefs.current[c] = el)}>
                {copies.map((_, copyIndex) =>
                  col.map((item, itemIndex) => renderTile(item, `${c}-${copyIndex}-${itemIndex}`, c))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <>
      {muro}
      {salto && createPortal(<div className="drift-wall__velo" aria-hidden="true" />, document.body)}
    </>
  );
};

export default MuroProyectos;
