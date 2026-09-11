"""Turntable de 360° del kiosco de guadua, para el visor de la portada.

Se ejecuta en Blender sin ventana:

    blender -b modelos-3d/blender/kiosco-sumak.blend \
        --python herramientas/render-kiosco-360.py -- \
        --motor eevee --fotogramas 6 --salida /tmp/prueba

El `.blend` es una EXPORTACIÓN DE REVIT, y eso manda en todo lo que sigue:

1. No trae un solo material y son 2348 objetos, de los cuales 2271 se llaman
   `MONTANTE 1` —cada guadua de los arcos y de la celosía es un objeto suelto—.
   Asignar a mano es imposible: los materiales se reparten por FAMILIA DE
   NOMBRE, que es el dato que sobrevivió a la exportación.
2. Sí trae UVs, pero son las de la exportación, no un desempaque: no sirven
   para colocar una textura. Todo aquí es procedural sobre coordenadas
   generadas, que no dependen de ellas ni de archivos externos.
3. Trae cinco objetos `Nivel …`, que son las ANOTACIONES de niveles de Revit.
   Uno de ellos está a 30 m del edificio y estira la caja de 7,7 × 8,2 m a
   25 × 30 m. Con la caja mal medida el centro de giro cae fuera del kiosco y
   el turntable sale como un barrido lateral. Se borran antes de medir nada.

El fondo va TRANSPARENTE a propósito: el visor (`Giratorio.astro`) dibuja WebP
con alfa sobre la portada. El atardecer del render de referencia entra por la
LUZ —sol bajo y cielo cálido—, no por un cielo pintado detrás.
"""
import bpy, sys, math, argparse, mathutils, bmesh

# ── 0 · argumentos ────────────────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument('--motor', default='cycles', choices=['cycles', 'eevee'])
ap.add_argument('--fotogramas', type=int, default=36)
ap.add_argument('--muestras', type=int, default=128)
ap.add_argument('--ancho', type=int, default=1400)
ap.add_argument('--alto', type=int, default=1050)
ap.add_argument('--salida', default='/tmp/kiosco-360')
ap.add_argument('--angulos', default='')   # prueba: lista de grados sueltos
ap.add_argument('--sol', type=float, default=5.0)
ap.add_argument('--cielo', type=float, default=0.15)
ap.add_argument('--exposicion', type=float, default=-0.9)
# Cuánto naranja lleva el sol: 1 es el atardecer pleno, 0 una luz neutra. El
# fondo del hero es un guadual en sombra —verde y difuso—, y un sol muy cálido
# encima del modelo lo despega de su escena por mucho que el recorte sea bueno.
ap.add_argument('--calidez', type=float, default=0.60)
# Elevación del sol DEL CIELO, que no es la del sol que proyecta sombra: son
# dos cosas distintas a propósito (ver el bloque de luz).
ap.add_argument('--cielo-elevacion', type=float, default=65.0)
# Relleno que acompaña a la cámara. 0 lo apaga.
# 0 por omisión: no aporta. Se montó para rescatar la celosía interior cuando
# el cielo subió a 65°, y medido no hace falta —con él, el contraste de volumen
# baja de 1,23 a 1,06 sin mejorar nada—. Se deja parametrizado porque el día
# que se cambie la elevación del cielo volverá a hacer falta.
ap.add_argument('--relleno', type=float, default=0.0)
ap.add_argument('--cota', type=float, default=-0.10)
ap.add_argument('--suelo', default='dados', choices=['placa', 'dados', 'nada'])
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

S = bpy.context.scene

# ── 1 · limpieza ──────────────────────────────────────────────────────────────
# Las anotaciones de Revit y el terreno. El terreno se va porque con fondo alfa
# un plano de suelo recortado deja un borde duro flotando bajo el edificio; la
# placa de concreto (`Suelo Concreto Pulido`) sí se queda, que es la que el
# render de referencia enseña.
FUERA = ('Nivel ', 'Superficie')
borrados = [o for o in bpy.data.objects if o.name.startswith(FUERA)]
for o in borrados:
    bpy.data.objects.remove(o, do_unlink=True)
print(f"· fuera {len(borrados)} objetos de anotación y terreno")


def recortar_bajo_cota(z):
    """Quita todo lo que en la obra va enterrado.

    El modelo trae la cimentación entera —zapatas, plataformas y el arranque
    empotrado de los arcos—, y en un render normal eso no se ve porque hay
    terreno tapándolo. Aquí no lo hay: el fotograma sale recortado sobre fondo
    transparente, así que las zapatas quedaban colgando en el aire bajo el
    edificio, como si el kiosco estuviera arrancado de cuajo.

    La cota es -0.10, que es la cara INFERIOR de la placa (`Suelo Concreto
    Pulido` va de -0.10 a 0.00). Cortar en 0.00 se comería la placa entera y
    dejaría el edificio sin piso; cortando en su cara de abajo, la placa se
    conserva completa y los dados de concreto siguen asomando sus 30 cm por
    encima, que es justo lo que enseña la fotografía de referencia.

    Barato: a esta cota solo 20 objetos cruzan el plano —los 5 dados y 15 arcos
    de lata—. Los 2270 culmos están enteros por encima y no se tocan, así que
    esto no es una pasada sobre la escena completa.
    """
    fuera, cortados = [], 0
    for o in [x for x in bpy.data.objects if x.type == 'MESH']:
        caja = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        if max(q.z for q in caja) <= z:
            fuera.append(o)
            continue
        if min(q.z for q in caja) >= z:
            continue

        # El plano va en coordenadas del MUNDO pero bmesh trabaja en las del
        # objeto, y estos vienen de Revit con matriz propia (rotación y la
        # escala 0.305 de pies a metros). La normal no se transforma con la
        # matriz sino con la inversa traspuesta: con escala no uniforme, usar
        # la matriz a secas deja el plano ladeado y el corte sale en diagonal.
        inv = o.matrix_world.inverted()
        co = inv @ mathutils.Vector((0.0, 0.0, z))
        no = (o.matrix_world.to_3x3().inverted().transposed()
              @ mathutils.Vector((0.0, 0.0, 1.0))).normalized()

        malla = bmesh.new()
        malla.from_mesh(o.data)
        r = bmesh.ops.bisect_plane(
            malla, geom=list(malla.verts) + list(malla.edges) + list(malla.faces),
            plane_co=co, plane_no=no, clear_inner=True)
        # Tapar el corte. Sin esto el arco queda como un tubo abierto y se le
        # ve el hueco negro por dentro desde los fotogramas bajos.
        bordes = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        if bordes:
            bmesh.ops.holes_fill(malla, edges=bordes)
        malla.to_mesh(o.data)
        malla.free()
        o.data.update()
        cortados += 1

    for o in fuera:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f'· bajo cota {z}: {len(fuera)} enterrados fuera, {cortados} recortados')


# QUÉ SE APOYA EN QUÉ. El modelo trae la placa de concreto sobre la que se
# levanta el kiosco, y en la portada el fotograma va recortado sobre la
# fotografía del guadual: ahí la placa es una losa blanca flotando en el aire,
# lo más claro del encuadre, compitiendo con el verde por la atención que le
# toca a la guadua.
#
# · `placa` deja la obra como está.
# · `dados` quita la placa y el kiosco se apoya en sus cinco basas de concreto,
#   que se leen como los pies del objeto. Es coherente con cómo cuenta el resto
#   del sitio: lo que no es guadua va como masa —la placa, la basa, el estribo—.
# · `nada` sube el corte por encima de las basas y deja solo guadua y paja.
SUELOS = {
    'placa': ((), args.cota),
    'dados': (('Suelo Concreto', 'Plataforma'), args.cota),
    'nada':  (('Suelo Concreto', 'Plataforma'), 0.32),
}
quitar, cota = SUELOS[args.suelo]
if quitar:
    fuera = [o for o in bpy.data.objects if o.name.startswith(quitar)]
    for o in fuera:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f'· suelo «{args.suelo}»: fuera {len(fuera)} piezas de placa')
recortar_bajo_cota(cota)

# ── 2 · materiales ────────────────────────────────────────────────────────────
def nodo(mat):
    mat.use_nodes = True
    a = mat.node_tree
    a.nodes.clear()
    sal = a.nodes.new('ShaderNodeOutputMaterial')
    pri = a.nodes.new('ShaderNodeBsdfPrincipled')
    a.links.new(pri.outputs['BSDF'], sal.inputs['Surface'])
    return a, pri

def material(nombre, color, rugosidad, *, variacion=0.0, relieve=0.0, escala=40.0,
             estirar=(1.0, 1.0, 1.0), moteado=0.0):
    """Principled con dos trucos que hacen el trabajo pesado.

    `variacion` usa Object Info → Random: Blender le da a cada objeto un número
    fijo entre 0 y 1. Con 2271 culmos compartiendo un solo material, es lo que
    impide que el haz se lea como plástico: cada guadua queda en un tono
    distinto, como en un guadual de verdad. Sin esto la celosía sale uniforme y
    delata el render al instante.

    `relieve` es ruido a bump. No hay normal map porque no hay UVs fiables (ver
    cabecera); el ruido procedural se orienta por coordenadas generadas y no
    necesita ninguna.

    `estirar` escala esas coordenadas de forma DESIGUAL antes del ruido, y es lo
    que separa la paja de una lona. Un ruido isótropo le da a la cubierta un
    picado parejo que a contraluz se lee como tela arrugada; estirándolo mucho
    en un eje, las manchas se alargan y pasan a leerse como fibras peinadas en
    una dirección, que es lo que hace un techo de paja de verdad.
    """
    mat = bpy.data.materials.new(nombre)
    a, pri = nodo(mat)
    pri.inputs['Base Color'].default_value = (*color, 1)
    pri.inputs['Roughness'].default_value = rugosidad

    if variacion:
        info = a.nodes.new('ShaderNodeObjectInfo')
        ram = a.nodes.new('ShaderNodeValToRGB')
        ram.color_ramp.elements[0].color = (*[c * (1 - variacion) for c in color], 1)
        ram.color_ramp.elements[1].color = (*[min(1, c * (1 + variacion)) for c in color], 1)
        a.links.new(info.outputs['Random'], ram.inputs['Fac'])
        a.links.new(ram.outputs['Color'], pri.inputs['Base Color'])

    if relieve:
        coord = a.nodes.new('ShaderNodeTexCoord')
        mapa = a.nodes.new('ShaderNodeMapping')
        mapa.inputs['Scale'].default_value = estirar
        rui = a.nodes.new('ShaderNodeTexNoise')
        rui.inputs['Scale'].default_value = escala
        rui.inputs['Detail'].default_value = 8.0
        bum = a.nodes.new('ShaderNodeBump')
        bum.inputs['Strength'].default_value = relieve
        # `Generated` Y NO `Object`, y esto costó encontrarlo. Las coordenadas
        # `Object` son las locales crudas, y en una exportación de Revit vienen
        # con el origen lejos del objeto y una escala de 0.305 —la conversión de
        # pies a metros, que quedó en la matriz—, así que su magnitud es de
        # cientos de unidades. Con eso, cualquier escala de ruido razonable cae
        # POR DEBAJO DEL PÍXEL, y un ruido sub-píxel no se ve como ruido: el
        # render promedia el gradiente y sale gris liso. El síntoma engaña —la
        # cubierta parecía lona sin relieve, como si el bump fuera flojo— cuando
        # el relieve estaba y era invisible. `Generated` va normalizado de 0 a 1
        # sobre la caja del propio objeto, así que la escala significa lo mismo
        # aquí que en cualquier otro modelo que llegue después.
        a.links.new(coord.outputs['Generated'], mapa.inputs['Vector'])
        a.links.new(mapa.outputs['Vector'], rui.inputs['Vector'])
        a.links.new(rui.outputs['Fac'], bum.inputs['Height'])
        a.links.new(bum.outputs['Normal'], pri.inputs['Normal'])
    if moteado and relieve:
        # EL MISMO RUIDO, TAMBIÉN AL COLOR. Un bump solo se ve donde la luz lo
        # roza; en la cara en sombra de la cubierta desaparece y la paja vuelve
        # a leerse como lona. Oscureciendo el color con el mismo ruido, la
        # fibra sigue ahí en la penumbra. Va después del degradado por objeto,
        # así que cada concha conserva su tono y encima lleva su veta.
        mez = a.nodes.new('ShaderNodeMix')
        mez.data_type = 'RGBA'
        mez.blend_type = 'MULTIPLY'
        mez.inputs['Factor'].default_value = moteado
        entrante = pri.inputs['Base Color'].links
        origen = entrante[0].from_socket if entrante else None
        if origen:
            a.links.new(origen, mez.inputs[6])
        else:
            mez.inputs[6].default_value = (*color, 1)
        a.links.new(rui.outputs['Color'], mez.inputs[7])
        a.links.new(mez.outputs[2], pri.inputs['Base Color'])
    return mat

def material_paja(nombre, color):
    """La cubierta, que necesita su propio material y no una variante del genérico.

    LA PAJA ERA LO QUE DELATABA EL RENDER: se leía como lona de plástico. El
    diagnóstico no era el color ni el relieve, sino que la superficie devolvía el
    cielo de forma PAREJA. Tres cosas lo arreglan, y las tres importan:

    1. CASI NADA DE ESPECULAR. El Principled trae IOR 1.5, que es vidrio-ish; la
       paja seca apenas brilla. Con el specular alto, la cubierta entera
       reflejaba el naranja del cielo en una lámina continua, y una lámina
       continua de brillo es exactamente lo que el ojo llama plástico.
    2. RUGOSIDAD QUE VARÍA. Ninguna superficie real tiene la misma rugosidad en
       dos centímetros seguidos. Es el remedio de fondo: rompe el reflejo en
       manchas en lugar de quitarlo.
    3. HILADAS EN COORDENADAS DE MUNDO. Las demás texturas de este archivo van
       sobre `Generated`, que se normaliza POR OBJETO —y las 25 conchas tienen
       cada una su orientación, así que la fibra salía en una dirección distinta
       en cada paño—. La paja no se instala así: se instala en hiladas
       horizontales, a cota constante, y una hilada cruza de una concha a la
       vecina sin enterarse de que son dos objetos. Tomando la Z de la posición
       en mundo las hiladas quedan alineadas en todo el edificio, y de paso la
       escala se mide en metros de verdad y no en fracciones de caja.
    """
    mat = bpy.data.materials.new(nombre)
    a, pri = nodo(mat)
    pri.inputs['Roughness'].default_value = 0.95
    pri.inputs['IOR'].default_value = 1.12          # (1)

    geo = a.nodes.new('ShaderNodeNewGeometry')      # posición en MUNDO

    # (3) Las hiladas. Periodo de unos 7 cm, que es una hilada de paja atada.
    # La distorsión las despeina: sin ella son un rayado de imprenta.
    hil = a.nodes.new('ShaderNodeTexWave')
    hil.wave_type = 'BANDS'
    hil.bands_direction = 'Z'
    hil.wave_profile = 'SIN'
    hil.inputs['Scale'].default_value = 14.0
    hil.inputs['Distortion'].default_value = 2.2
    hil.inputs['Detail'].default_value = 4.0
    hil.inputs['Detail Scale'].default_value = 1.4
    a.links.new(geo.outputs['Position'], hil.inputs['Vector'])

    # El grano de los tallos sueltos, de unos 4 mm. Esto es lo que a un metro de
    # distancia hace que la hilada tenga espesor en vez de ser una raya pintada.
    tal = a.nodes.new('ShaderNodeTexNoise')
    tal.inputs['Scale'].default_value = 110.0
    tal.inputs['Detail'].default_value = 10.0
    tal.inputs['Roughness'].default_value = 0.6
    a.links.new(geo.outputs['Position'], tal.inputs['Vector'])

    # Las manchas grandes: zonas más claras y más oscuras del orden del metro,
    # de la paja que se secó distinto. Sin ellas la cubierta vuelve a ser un
    # plano de un solo color por mucho grano fino que lleve encima.
    man = a.nodes.new('ShaderNodeTexNoise')
    # Manchas de unos 20 cm y no de medio metro. A escala 2.2 eran tan grandes
    # que en un paño de cubierta cabían tres o cuatro, y con el contraste que
    # tenían se leían como manchas de camuflaje sobre una lona en vez de como
    # paja secada de forma desigual.
    man.inputs['Scale'].default_value = 5.0
    man.inputs['Detail'].default_value = 4.0
    a.links.new(geo.outputs['Position'], man.inputs['Vector'])

    # Color: base oscura, aclarada por las manchas y ensuciada por el grano.
    ramp = a.nodes.new('ShaderNodeValToRGB')
    # RANGO ESTRECHO. Iba de 0.8 a 1.9 veces el color base —más del doble de
    # claro a oscuro—, y ese salto es lo que convertía una variación de secado
    # en dos materiales distintos conviviendo en el mismo paño. De 0.9 a 1.3 la
    # cubierta sigue sin ser un plano de un solo color y ya no se parcha.
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (*[c * 0.9 for c in color], 1)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (*[min(1, c * 1.35) for c in color], 1)
    a.links.new(man.outputs['Fac'], ramp.inputs['Fac'])

    suc = a.nodes.new('ShaderNodeMix')
    suc.data_type = 'RGBA'
    suc.blend_type = 'MULTIPLY'
    suc.inputs[0].default_value = 0.22
    a.links.new(ramp.outputs['Color'], suc.inputs[6])
    a.links.new(tal.outputs['Color'], suc.inputs[7])
    a.links.new(suc.outputs[2], pri.inputs['Base Color'])

    # (2) La rugosidad sigue a las hiladas: el canto de cada hilada, más
    # peinado, brilla un pelo; el hueco entre hiladas es mate del todo.
    rug = a.nodes.new('ShaderNodeMapRange')
    rug.inputs['To Min'].default_value = 0.62
    rug.inputs['To Max'].default_value = 1.0
    a.links.new(hil.outputs['Fac'], rug.inputs['Value'])
    a.links.new(rug.outputs['Result'], pri.inputs['Roughness'])

    # Relieve en dos escalas, sumadas: la hilada da la sombra grande —el
    # escalón de una sobre otra— y el grano la micro-sombra de los tallos. Un
    # bump de una sola escala se lee como abolladura, no como fibra.
    b1 = a.nodes.new('ShaderNodeBump')
    b1.inputs['Strength'].default_value = 1.0
    b1.inputs['Distance'].default_value = 0.04
    a.links.new(hil.outputs['Fac'], b1.inputs['Height'])

    b2 = a.nodes.new('ShaderNodeBump')
    b2.inputs['Strength'].default_value = 0.28
    b2.inputs['Distance'].default_value = 0.010
    a.links.new(tal.outputs['Fac'], b2.inputs['Height'])
    a.links.new(b1.outputs['Normal'], b2.inputs['Normal'])   # encadenados
    a.links.new(b2.outputs['Normal'], pri.inputs['Normal'])
    return mat


# El color no se inventa: sale del manual de marca por parentesco —la guadua
# cruda es `--cruda`— y de lo que enseña la fotografía de referencia.
MATERIALES = {
    'guadua':   material('MEG guadua',  (0.62, 0.40, 0.13), 0.38, variacion=0.22,
                         relieve=0.14, escala=5, estirar=(1.0, 1.0, 9.0), moteado=0.10),
    'lata':     material('MEG lata',    (0.50, 0.33, 0.13), 0.52, variacion=0.14,
                         relieve=0.12, escala=5, estirar=(1.0, 1.0, 9.0), moteado=0.10),
    'paja':     material_paja('MEG paja', (0.30, 0.175, 0.09)),
    # Gris de obra, no blanco. A 0.52 las zapatas salían lechosas y se comían
    # la atención que le toca a la guadua: en la portada iban sobre la
    # fotografía del guadual y eran lo más claro del encuadre.
    # Más oscuro todavía: con el ambiente subido, a 0.34 las basas pasaron a ser
    # el objeto más claro del encuadre —y el único frío—, y el ojo iba a ellas
    # antes que a la guadua. Son el apoyo, no el asunto.
    'concreto': material('MEG concreto',(0.23, 0.21, 0.18), 0.80, relieve=0.06, escala=14),
}

# Cada familia de Revit a su material. El orden importa: se toma la PRIMERA
# clave que sea prefijo del nombre.
REPARTO = [
    ('MONTANTE',                'guadua'),
    ('V_01_RECTANGULAR_LATAS',  'lata'),
    ('Muro básico',             'paja'),     # las conchas de cubierta
    ('C_10_RECTANGULAR_HORMIG', 'concreto'),
    ('Zapata',                  'concreto'),
    ('Plataforma',              'concreto'),
    ('Suelo Concreto',          'concreto'),
]
cuenta = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for prefijo, clave in REPARTO:
        if o.name.startswith(prefijo):
            o.data.materials.clear()
            o.data.materials.append(MATERIALES[clave])
            cuenta[clave] = cuenta.get(clave, 0) + 1
            break
print('· materiales:', cuenta)

# ── 3 · luz ───────────────────────────────────────────────────────────────────
for o in [o for o in bpy.data.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(o, do_unlink=True)

# Cielo de atardecer en el mundo. Ilumina aunque el fondo salga transparente:
# `film_transparent` recorta el cielo de la imagen, NO lo apaga como fuente de
# luz. Es lo que mete el naranja en la paja y el azul en las sombras.
S.world = S.world or bpy.data.worlds.new('World')
S.world.use_nodes = True
w = S.world.node_tree
w.nodes.clear()
wsal = w.nodes.new('ShaderNodeOutputWorld')
wfon = w.nodes.new('ShaderNodeBackground')
wcie = w.nodes.new('ShaderNodeTexSky')
# Blender 5 renombró el cielo de Nishita: el mismo modelo atmosférico se llama
# ahora `MULTIPLE_SCATTERING`. Se elige el que exista para que el script corra
# igual en 4.x y en 5.x.
_tipos = [i.identifier for i in wcie.bl_rna.properties['sky_type'].enum_items]
wcie.sky_type = 'MULTIPLE_SCATTERING' if 'MULTIPLE_SCATTERING' in _tipos else 'NISHITA'
# EL CIELO VA ALTO AUNQUE EL SOL VAYA RASANTE, y los dos números están
# desacoplados a propósito.
#
# Estuvo a 6°, igual que el sol, y ahí el domo de Nishita NO ES UN RELLENO: a
# esa elevación casi toda su luz sale de una banda de horizonte estrecha y
# naranja, en el mismo acimut del sol. El hemisferio contrario no recibe casi
# nada. Eso tiene dos consecuencias que costó ver:
#
# · Subir el cielo bajando el sol no equilibraba nada —se estaba echando más
#   luz POR EL MISMO LADO—, y por eso tres balances distintos salieron
#   prácticamente idénticos.
# · Como la cámara orbita y el sol es fijo, el modelo latía: medido sobre los
#   cuatro cuadrantes, la luminancia media iba de 45 a 131 —tres veces— y en
#   los ángulos a contraluz la mediana del modelo caía POR DEBAJO de la del
#   fondo. Medio turntable se hundía en la fotografía.
#
# A 65° el domo pasa de banda a cúpula casi uniforme: sube los fotogramas
# oscuros sin tocar los claros. El latido baja de 3,0× a 1,3×.
#
# Físicamente es incoherente —un cielo de mediodía con un rayo de las seis de
# la tarde—, y da igual: el fotograma sale recortado sobre fondo transparente y
# no hay horizonte con el que comparar. Lo que se lee es un claro de luz
# entrando en un guadual, que es justo la escena de la portada.
#
# OJO AL RECALIBRAR: la irradiancia del Nishita cambia muchísimo con la
# elevación y no de forma lineal. Tocar este número sin recalibrar `--cielo` da
# resultados desastrosos, y además en la dirección del problema original.
wcie.sun_elevation = math.radians(args.cielo_elevacion)

# EL SOL DE VERDAD ESTÁ AQUÍ DENTRO, y conviene saberlo antes de tocar nada.
#
# El cielo de Nishita trae el DISCO SOLAR incrustado en la textura: no es un
# fondo difuso, es un cielo con su sol, y ese sol ilumina. Es, con diferencia,
# la fuente dominante de esta escena: medido, apagando las DOS lámparas de
# abajo —sol y relleno a cero— el modelo sale prácticamente idéntico. Si estás
# subiendo `--sol` y no ves cambios, es por esto y no porque la lámpara falle.
#
# SE PROBÓ A APAGARLO (`wcie.sun_disc = False`) para dejar el domo como
# ambiente puro y que mandaran las lámparas, que es lo que pide el manual. Sale
# peor, y bastante: midiendo los mismos cuatro ángulos, el contraste de volumen
# cae de 1,06 a 0,54 y la saturación de las zonas claras de 0,41 a 0,28, con el
# mismo latido. El motivo es que el sol del Nishita no viene solo: viene con su
# atmósfera, así que su color cálido y el azul del domo que lo rodea están
# calculados juntos. Dos lámparas con colores puestos a mano no reproducen esa
# relación, y lo que se pierde es justamente el color de las luces.
#
# Así que el disco se queda. Las lámparas de abajo son el ajuste fino.
wcie.sun_rotation = math.radians(-35)
wcie.altitude = 300
# LA EXPOSICIÓN ES LO QUE DECIDE SI ESTO PARECE FOTOGRAFÍA O MAQUETA. Con el
# sol a 6 y el cielo a 1.2 —el primer intento— la guadua salía casi blanca: el
# amarillo miel se iba a la zona quemada de la curva y el edificio entero se
# leía en pasteles. El cielo de Nishita a 6° de elevación ya aporta mucha luz
# ambiente por sí solo, así que el sol NO tiene que competir con él.
#
# Y no baja de 0.6, que es lo que rescata el flanco en sombra. Con el sol fijo
# hay siempre una cara a contraluz, y como el fotograma sale recortado sobre la
# fotografía del guadual —oscura— esa cara se hundía en negro y el kiosco
# perdía media silueta contra el fondo. El cielo es aquí el relleno.
wfon.inputs['Strength'].default_value = args.cielo
w.links.new(wcie.outputs['Color'], wfon.inputs['Color'])
w.links.new(wfon.outputs['Background'], wsal.inputs['Surface'])

sol_d = bpy.data.lights.new('Sol', 'SUN')
# A 3.0 la cara al sol se quemaba: la fibra perdía su relieve justo donde más
# debería verse —el bump solo existe si hay gradiente de luz, y en la zona
# saturada no lo hay— y el canto iluminado cortaba contra la sombra como si
# fueran dos materiales. A 2.0, con el cielo subido para que el flanco en
# sombra no se hunda, la hilada se lee en toda la cubierta.
sol_d.energy = args.sol
_c = max(0.0, min(1.0, args.calidez))
sol_d.color = (1.0, 0.72 + 0.28 * (1 - _c), 0.45 + 0.55 * (1 - _c))
sol_d.angle = math.radians(1.5)         # sombras con borde suave, no de calco
sol = bpy.data.objects.new('Sol', sol_d)
S.collection.objects.link(sol)
# Orientación de partida del sol, en el marco del MUNDO: 78° desde el cenit
# —o sea, rasante— y girado 55°.
SOL_INCLINACION = 78.0
SOL_ACIMUT = 55.0
sol.rotation_euler = (math.radians(SOL_INCLINACION), 0, math.radians(SOL_ACIMUT))

# EL RELLENO, y este SÍ acompaña a la cámara.
#
# Con el cielo alto, lo que se apagaba era el interior: la celosía bajo la
# cubierta se iba a negro porque ningún rayo entra por debajo de un domo. Este
# es un sol muy rasante —10° sobre el horizonte— y muy ancho: `angle` de 60°
# convierte la fuente en un disco enorme, así que no proyecta sombra
# reconocible y no se lee como un segundo sol, sino como el reflejo del claro
# que hay alrededor.
#
# Que gire con la cámara no contradice el sol fijo: el fijo es el que modela y
# proyecta, y sigue fijo. Este solo garantiza que la cara que se está mirando
# nunca esté del todo apagada, que es la otra mitad de quitarle el latido al
# giro.
#
# `angle` tan abierto es RUIDOSO: por debajo de unas 200 muestras se ve grano
# en la penumbra. No bajes de ahí en la pasada buena.
relleno_d = bpy.data.lights.new('Relleno', 'SUN')
relleno_d.energy = args.relleno
relleno_d.color = (1.0, 0.95, 0.88)
relleno_d.angle = math.radians(60)
relleno = bpy.data.objects.new('Relleno', relleno_d)
S.collection.objects.link(relleno)

# AgX es el transformado de vista por omisión desde Blender 4 y desatura a
# propósito para salvar las altas luces. En un objeto que vive de un solo color
# —la guadua— eso se nota como desvaído, así que va con el «look» contrastado y
# un pelo de exposición abajo. `Standard` quemaría el borde iluminado del culmo.
S.view_settings.view_transform = 'AgX'
try:
    S.view_settings.look = 'AgX - Punchy'
except TypeError:
    pass
S.view_settings.exposure = args.exposicion

# ── 4 · encuadre y órbita ─────────────────────────────────────────────────────
mallas = [o for o in bpy.data.objects if o.type == 'MESH']
pts = [o.matrix_world @ mathutils.Vector(c) for o in mallas for c in o.bound_box]
mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
centro = (mn + mx) / 2
radio = (mx - mn).length / 2
print(f"· caja {[round(v,2) for v in (mx-mn)]}  centro {[round(v,2) for v in centro]}")

# ENCUADRE — los tres números que deciden si se parece a la fotografía.
ELEVACION = 12.0     # grados sobre el horizonte
DISTANCIA = 2.3      # múltiplo del radio de la caja
LENTE     = 50.0     # mm
MIRA_A    = 0.38     # a qué altura de la caja apunta, 0 = suelo, 1 = cumbre

cam_d = bpy.data.cameras.new('CamOrbita')
cam_d.lens = LENTE
cam = bpy.data.objects.new('CamOrbita', cam_d)
S.collection.objects.link(cam)
S.camera = cam

objetivo = mathutils.Vector((centro.x, centro.y, mn.z + (mx.z - mn.z) * MIRA_A))

def orientar_sol(grados):
    """Dónde está el sol en el fotograma que mira al edificio desde `grados`.

    AQUÍ SE DECIDE SI EL GIRO ES UN EDIFICIO O UN OBJETO. El modelo da la
    vuelta, pero el sol no tiene por qué acompañarlo, y las dos opciones dicen
    cosas distintas:

    · SOL FIJO EN EL MUNDO (no tocar nada): es una órbita de verdad alrededor de
      algo que está quieto bajo un cielo. Unos fotogramas quedan a contraluz
      —la paja se enciende por el borde, el interior en penumbra— y otros de
      frente. Se siente un lugar; el precio es que el brillo late a lo largo del
      arrastre, y como el visitante controla el giro con el cursor, ese latido
      queda bajo su mano.

    · SOL SOLIDARIO CON LA CÁMARA (sumarle `grados` al acimut): los 36
      fotogramas se iluminan igual, el modelo se lee siempre con el mismo
      contraste y el arrastre es una superficie lisa. Se siente un objeto sobre
      una mesa, no un edificio en un sitio: es lo que hace un configurador de
      producto.

    · Y hay un término medio: seguir a la cámara solo en parte —la mitad del
      giro, por ejemplo— para conservar algo de cambio sin que ningún fotograma
      se apague del todo.

    VA FIJO. El modelo sale recortado sobre fondo transparente, y eso le quita
    casi todo el precio a la opción: sin cielo detrás, el contraluz no se lee
    como un cambio de hora —no hay horizonte con el que compararlo— sino como
    brillo en el canto de la paja. Queda el latido de brillo a lo largo del
    arrastre, y ahí es un rasgo: el kiosco responde a la mano como respondería
    un objeto de verdad al que se le da la vuelta.

    El relleno sí usa `grados`: ver su bloque más arriba.

    CUIDADO CON EL ACIMUT. El convenio de `rotation_euler` de un SUN aquí va
    desfasado respecto de lo que uno escribiría: poner el relleno «a 40° de la
    cámara» de la forma obvia lo deja DETRÁS del modelo y parece que la luz no
    hace nada. Los +100 están medidos, no deducidos.
    """
    sol.rotation_euler = (math.radians(SOL_INCLINACION), 0, math.radians(SOL_ACIMUT))
    if args.relleno:
        relleno.rotation_euler = (math.radians(80), 0, math.radians(grados + 100))


def situar(grados):
    a = math.radians(grados)
    e = math.radians(ELEVACION)
    d = radio * DISTANCIA
    cam.location = objetivo + mathutils.Vector(
        (math.cos(a) * d * math.cos(e), math.sin(a) * d * math.cos(e), d * math.sin(e)))
    cam.rotation_euler = (objetivo - cam.location).to_track_quat('-Z', 'Y').to_euler()

# ── 5 · render ────────────────────────────────────────────────────────────────
S.render.resolution_x, S.render.resolution_y = args.ancho, args.alto
S.render.resolution_percentage = 100
S.render.film_transparent = True                 # el alfa que espera el visor
S.render.image_settings.file_format = 'PNG'
S.render.image_settings.color_mode = 'RGBA'
S.render.image_settings.compression = 15

if args.motor == 'cycles':
    S.render.engine = 'CYCLES'
    S.cycles.samples = args.muestras
    S.cycles.use_denoising = True
    S.cycles.max_bounces = 6                     # celosía: no hace falta más
    S.cycles.transparent_max_bounces = 4
    # `S.cycles.device = 'GPU'` POR SÍ SOLO NO USA LA GPU: es solo la
    # intención de la escena. Quien decide es el backend elegido en las
    # preferencias del complemento, y en `blender -b` viene sin elegir, así que
    # sin esto Cycles cae a CPU en silencio —el render sale igual, solo que
    # varias veces más lento y sin que nada lo diga—. OptiX antes que CUDA: en
    # una escena de 2271 objetos los núcleos RT se notan.
    pref = bpy.context.preferences.addons['cycles'].preferences
    for tipo in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            pref.compute_device_type = tipo
            pref.get_devices()
            usables = [d for d in pref.devices if d.type == tipo]
            if usables:
                for d in pref.devices:
                    d.use = (d.type == tipo)
                S.cycles.device = 'GPU'
                print(f"· Cycles en GPU ({tipo}): {usables[0].name}")
                break
        except (TypeError, AttributeError):
            continue
    else:
        print('· Cycles en CPU')
else:
    S.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [
        i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items
    ] else 'BLENDER_EEVEE'

# El reparto de ángulos es REGULAR y el visor lo cuenta así: `giratorioArrastre`
# mapea el recorrido del cursor a índice de fotograma linealmente. Un turntable
# con pasos desiguales se sentiría como si el modelo frenara en algún cuadrante.
if args.angulos:
    pasos = [(i, float(g)) for i, g in enumerate(args.angulos.split(','))]
else:
    pasos = [(i, i * 360.0 / args.fotogramas) for i in range(args.fotogramas)]

for i, grados in pasos:
    situar(grados)
    orientar_sol(grados)
    S.render.filepath = f"{args.salida}/bruto-{i:03d}.png"
    bpy.ops.render.render(write_still=True)
    print(f"· {i:03d} · {grados:6.1f}°")
print(f"listo · {len(pasos)} fotogramas en {args.salida}")
