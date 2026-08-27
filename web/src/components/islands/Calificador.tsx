import { useEffect, useMemo, useRef, useState } from 'react';
import './calificador.css';

export type Paso = {
  id: string;
  pregunta: string;
  opciones: string[];
  /**
   * Vista del visor que se muestra al enfocar cada opción, por índice.
   * Solo lo usa el primer paso; el resto no necesita ilustración.
   */
  vistas?: (string | null)[];
  /**
   * Preguntas que siguen a cada opción, por índice. Solo lo usa el primer paso:
   * es la bifurcación de la portada, donde «Comprar guadua» tiene que seguir
   * por cantidad y despacho y no por metros cuadrados.
   */
  ramas?: Paso[][];
  /**
   * Primera línea del mensaje según la opción elegida, por índice. Solo lo usa
   * el primer paso; si falta, manda el `contexto` de la página.
   */
  contextos?: (string | null)[];
  /**
   * Etiqueta con la que la respuesta aparece en el mensaje de WhatsApp.
   * Sin etiqueta, las respuestas se encadenan separadas por «·» — más compacto,
   * suficiente cuando las opciones se explican solas. Con etiqueta, cada una
   * ocupa su renglón, que es lo que sirve para cotizar material.
   */
  etiqueta?: string;
};

interface Props {
  whatsapp: string;
  pasos: Paso[];
  /**
   * Permite que un botón de fuera preseleccione la primera respuesta.
   * Mapea el valor de `data-intencion` a una opción del primer paso.
   */
  preseleccion?: Record<string, string>;
  /**
   * Primera línea del mensaje cuando el primer paso no trae `contextos`.
   * Es lo que distingue los dos embudos en el chat de Megudan.
   */
  contexto?: string;
}

/**
 * Avisa al visor de al lado qué está mirando el visitante. Se comunica por
 * evento del DOM y no por props para no meter el panel dentro de la isla:
 * así el texto sigue siendo HTML estático y solo el calificador lleva React.
 */
function avisar(seccion: HTMLElement | null, vista: string | null) {
  seccion?.dispatchEvent(
    new CustomEvent('calificador:vista', { detail: { vista }, bubbles: false }),
  );
}

export default function Calificador({ whatsapp, pasos, preseleccion, contexto }: Props) {
  const [paso, setPaso] = useState(0);
  const [respuestas, setRespuestas] = useState<Record<string, string>>({});
  const [nombre, setNombre] = useState('');
  const [telefono, setTelefono] = useState('');
  const raiz = useRef<HTMLDivElement>(null);

  const seccion = () => raiz.current?.closest<HTMLElement>('[data-visor-raiz]') ?? null;

  // Un clic en «Quiero construir con guadua» debe llegar aquí con el paso 1 resuelto.
  useEffect(() => {
    if (!preseleccion) return;
    function alClic(e: MouseEvent) {
      const disparador = (e.target as HTMLElement).closest<HTMLElement>('[data-intencion]');
      if (!disparador) return;
      const valor = preseleccion![disparador.dataset.intencion!];
      if (!valor) return;
      setRespuestas({ [pasos[0].id]: valor });
      setPaso(1);
    }
    document.addEventListener('click', alClic);
    return () => document.removeEventListener('click', alClic);
  }, [preseleccion, pasos]);

  // Al avanzar de paso el visor vuelve a reposo: la ilustración pertenece a
  // la pregunta que se está respondiendo, no a la siguiente.
  useEffect(() => {
    avisar(seccion(), null);
  }, [paso]);

  /**
   * Índice de la opción elegida en el primer paso: gobierna la rama y la línea
   * de contexto. -1 mientras nadie ha respondido.
   */
  const rama = pasos[0].opciones.indexOf(respuestas[pasos[0].id]);

  /**
   * Las preguntas que se están haciendo de verdad. Si la opción elegida trae
   * ramal, sustituye la cola declarada; si no, se queda la de por defecto.
   */
  const secuencia = useMemo(() => {
    const cola = rama >= 0 ? pasos[0].ramas?.[rama] : undefined;
    return cola ? [pasos[0], ...cola] : pasos;
  }, [pasos, rama]);

  const total = secuencia.length + 1; // las preguntas más el paso de datos
  const enDatos = paso === secuencia.length;

  const mensaje = useMemo(() => {
    const entrada = pasos[0].contextos?.[rama] ?? contexto;
    const lineas: string[] = [
      `Hola Megudan, soy ${nombre.trim() || '—'}.${entrada ? ` ${entrada}` : ''}`,
    ];

    // Las respuestas sin etiqueta se juntan en un solo renglón; las etiquetadas
    // van una por renglón. Así el mismo componente sirve a los dos formatos.
    const sueltas: string[] = [];
    for (const p of secuencia) {
      const r = respuestas[p.id];
      if (!r) continue;
      // La opción que ya puso la línea de contexto no se repite abajo: en la
      // rama de compra se leía «Quiero comprar guadua.» y debajo, solo,
      // «Comprar guadua».
      if (p === pasos[0] && pasos[0].contextos?.[rama]) continue;
      if (p.etiqueta) lineas.push(`${p.etiqueta}: ${r}`);
      else sueltas.push(r);
    }
    if (sueltas.length) lineas.splice(1, 0, sueltas.join(' · '));
    if (telefono.trim()) lineas.push(`Tel: ${telefono.trim()}`);

    return lineas.join('\n');
  }, [respuestas, nombre, telefono, secuencia, pasos, rama, contexto]);

  const listo = nombre.trim().length > 1 && telefono.trim().length >= 7;

  function responder(actual: Paso, opcion: string) {
    // Cambiar de rama en el primer paso descarta lo respondido en la anterior:
    // esas preguntas ya no se van a hacer y no deben viajar en el mensaje.
    const cambiaRama = actual === pasos[0] && respuestas[actual.id] !== opcion;
    setRespuestas((r) => (cambiaRama ? { [actual.id]: opcion } : { ...r, [actual.id]: opcion }));
    setPaso((p) => p + 1);
  }

  return (
    <div className="cal" ref={raiz}>
      {/* El avance se reemplaza sin recargar: sin esto un lector de pantalla no
          informa que la pregunta cambió y el visitante no sabe si funcionó. */}
      <p className="cal-sr" aria-live="polite">
        Paso {paso + 1} de {total}
        {enDatos ? ': tus datos' : `: ${secuencia[paso].pregunta}`}
      </p>

      <div className="cal-barra" aria-hidden="true">
        {Array.from({ length: total }, (_, i) => (
          <span key={i} className={i <= paso ? 'tramo hecho' : 'tramo'} />
        ))}
      </div>

      {!enDatos ? (
        <fieldset className="cal-paso">
          <legend>
            <span className="rotulo">Paso {paso + 1} de {total}</span>
            <h3>{secuencia[paso].pregunta}</h3>
          </legend>
          <div className="cal-opciones">
            {secuencia[paso].opciones.map((o, i) => (
              <button
                key={o}
                type="button"
                className={`opcion boton-guadua${respuestas[secuencia[paso].id] === o ? ' elegida' : ''}`}
                onClick={() => responder(secuencia[paso], o)}
                onMouseEnter={() => avisar(seccion(), secuencia[paso].vistas?.[i] ?? null)}
                onFocus={() => avisar(seccion(), secuencia[paso].vistas?.[i] ?? null)}
                onMouseLeave={() => avisar(seccion(), null)}
                onBlur={() => avisar(seccion(), null)}
              >
                {o}
              </button>
            ))}
          </div>
        </fieldset>
      ) : (
        <fieldset className="cal-paso">
          <legend>
            <span className="rotulo">Paso {total} de {total}</span>
            <h3>Tus datos</h3>
          </legend>
          <div className="cal-campos">
            <label>
              <span>Nombre</span>
              <input value={nombre} onChange={(e) => setNombre(e.target.value)} autoComplete="name" />
            </label>
            <label>
              <span>Teléfono</span>
              <input
                type="tel"
                value={telefono}
                onChange={(e) => setTelefono(e.target.value)}
                inputMode="tel"
                autoComplete="tel"
                spellCheck={false}
              />
            </label>
          </div>

          <p className="rotulo">Mensaje que le llega a Megudan</p>
          <pre className="cal-vista">{mensaje}</pre>

          <a
            className={`cal-enviar boton-guadua${listo ? '' : ' inactivo'}`}
            href={`https://wa.me/${whatsapp}?text=${encodeURIComponent(mensaje)}`}
            target="_blank"
            rel="noopener"
            aria-disabled={!listo}
            onClick={(e) => { if (!listo) e.preventDefault(); }}
          >
            Enviar por WhatsApp
          </a>
          {!listo && <p className="cal-aviso">Escribe tu nombre y un teléfono para continuar.</p>}
        </fieldset>
      )}

      {paso > 0 && (
        <button type="button" className="cal-atras" onClick={() => setPaso((p) => p - 1)}>
          ← Volver
        </button>
      )}
    </div>
  );
}
