#!/usr/bin/env python3
"""
Genera una ficha visual (infografia) por artículo.

Cada página del sitio queda con su propia imagen:
  - Modelos    -> tarjeta con precio, consumo, potencia y costo mensual
  - Trámites   -> tarjeta con costo y pasos clave
  - Eléctricos -> tarjeta comparativa
  - Comparativas -> tarjeta con el veredicto
  - Costos/Compra -> tarjeta con el dato principal

Salida: dist/img/ficha-<slug>.png a 1200x675 (formato Open Graph).
"""
import json
import os
import re
import glob

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "assets", "img")
os.makedirs(OUT, exist_ok=True)

BG = "#0d0f12"
CARD = "#161c24"
CARD2 = "#1c242e"
TX = "#e8edf2"
MUT = "#c2ccd6"
DIM = "#8b97a4"
ACC = "#e8b93b"
ACC2 = "#3ba55d"
AZUL = "#5b9bd5"
MORADO = "#9b7fd4"
ROJO = "#e06c5a"

W, H = 12.0, 6.75  # pulgadas a 100 dpi = 1200x675


def lona():
    fig = plt.figure(figsize=(W, H))
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_facecolor(BG)
    return fig, ax


def cabecera(fig, ax, etiqueta, color=ACC):
    ax.add_line(Line2D([3, 9], [95.4, 95.4], color=color, lw=4.5,
                       solid_capstyle="round", zorder=5))
    fig.text(0.035, 0.958, etiqueta.upper(), color=color, fontsize=11,
             fontweight="bold", va="top", ha="left", zorder=5)
    fig.text(0.965, 0.958, "cuantocuesta.xyz", color=DIM, fontsize=9.5,
             va="top", ha="right", zorder=5)


def bloque(ax, x, y, w, h, color=CARD, radio=1.2, borde=None):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radio}",
                       facecolor=color,
                       edgecolor=borde if borde else color,
                       linewidth=1.4 if borde else 0, zorder=2)
    ax.add_patch(p)
    return p


def dato(ax, x, y, w, h, valor, etiqueta, color=ACC):
    """Cajita con un numero grande y su etiqueta debajo."""
    bloque(ax, x, y, w, h, CARD2)
    ax.text(x + w / 2, y + h * 0.60, valor, ha="center", va="center",
            color=color, fontsize=25, fontweight="bold", zorder=6)
    ax.text(x + w / 2, y + h * 0.24, etiqueta, ha="center", va="center",
            color=MUT, fontsize=10.5, zorder=6)


def pie(fig, texto):
    fig.text(0.035, 0.045, texto, color=DIM, fontsize=8.6,
             va="bottom", ha="left", zorder=5)


def guardar(fig, nombre):
    ruta = os.path.join(OUT, nombre)
    fig.savefig(ruta, dpi=100, facecolor=BG, edgecolor="none")
    plt.close(fig)
    return ruta


# ============================================================ MODELOS
MODELOS = {
    "kia-soluto": dict(
        marca="Kia", modelo="Soluto", segmento="Sedán B",
        claim="El auto de pasajeros más vendido del Ecuador",
        ventas="8.725 unidades en 2025",
        datos=[("$15.799", "precio desde", ACC2), ("15,5 km/l", "consumo mixto", ACC2),
               ("$168", "costo al mes", ACC), ("94 hp", "potencia", MUT)],
        nota="Garantía 10 años o 160.000 km"),

    "chevrolet-dmax": dict(
        marca="Chevrolet", modelo="D-Max", segmento="Camioneta 4x4",
        claim="La camioneta más vendida del país",
        ventas="5.515 unidades en 2025",
        datos=[("$34.000", "precio desde", ACC2), ("#1", "en camionetas", ACC),
               ("$345", "costo al mes", ACC), ("4x4", "tracción", MUT)],
        nota="Líder absoluto del segmento de camionetas"),

    "chevrolet-groove": dict(
        marca="Chevrolet", modelo="Groove", segmento="SUV compacto",
        claim="El SUV más vendido de Ecuador",
        ventas="4.063 unidades en 2025",
        datos=[("$19.999", "precio desde", ACC2), ("14,0 km/l", "consumo mixto", ACC2),
               ("$213", "costo al mes", ACC), ("98 hp", "potencia", MUT)],
        nota="Cuota desde $309 al mes con financiamiento"),

    "gwm-poer": dict(
        marca="GWM", modelo="Poer", segmento="Camioneta 4x4",
        claim="La única camioneta del top 10 ensamblada en Ecuador",
        ventas="4.092 unidades en 2025",
        datos=[("$27.000", "precio desde", ACC2), ("Ambato", "ensamblaje", ACC2),
               ("$303", "costo al mes", ACC), ("+53,7%", "crecimiento 2026", MORADO)],
        nota="Precio más bajo que las camionetas japonesas equivalentes"),

    "kia-sonet": dict(
        marca="Kia", modelo="Sonet", segmento="SUV subcompacto",
        claim="Ensamblado en Quito, con 6 airbags de serie",
        ventas="3.593 unidades en 2025",
        datos=[("$21.599", "precio desde", ACC2), ("18,03 km/l", "consumo IVT", ACC2),
               ("$220", "costo al mes", ACC), ("6", "airbags de serie", MUT)],
        nota="Repuestos locales gracias al ensamblaje nacional"),

    "kia-sportage": dict(
        marca="Kia", modelo="Sportage", segmento="SUV mediano",
        claim="El SUV mediano de referencia en Ecuador",
        ventas="2.512 unidades en 2025",
        datos=[("2.512", "unidades en 2025", ACC), ("SUV", "segmento", MUT),
               ("$500-700", "mantenimiento/año", ACC2), ("2.5 L", "motor", MUT)],
        nota="Comparte plataforma con el Hyundai Tucson"),

    "kia-seltos": dict(
        marca="Kia", modelo="Seltos", segmento="SUV compacto",
        claim="El hermano menor del Sportage",
        ventas="2.452 unidades en 2025",
        datos=[("2.452", "unidades en 2025", ACC), ("SUV", "segmento", MUT),
               ("Kia", "marca líder 2025", ACC2), ("+38%", "Kia en 2026", MORADO)],
        nota="Kia lideró el mercado 2025 con 19.141 unidades"),

    "hyundai-tucson": dict(
        marca="Hyundai", modelo="Tucson", segmento="SUV mediano",
        claim="Orientado al confort familiar",
        ventas="2.395 unidades en 2025",
        datos=[("$32.499", "precio desde", ACC2), ("2.5 L", "motor atmosférico", MUT),
               ("$335", "costo al mes", ACC), ("5 años", "garantía sin límite", ACC2)],
        nota="Comparte plataforma con el Kia Sportage"),

    "hyundai-grand-i10": dict(
        marca="Hyundai", modelo="Grand i10", segmento="Hatchback A",
        claim="El más económico de mantener del mercado",
        ventas="1.690 unidades en 2025",
        datos=[("$13.990", "precio desde", ACC2), ("$150", "costo al mes", ACC2),
               ("Bajo", "consumo", ACC2), ("1.2 L", "motor", MUT)],
        nota="La opción de entrada para primer auto"),

    "chery-arrizo": dict(
        marca="Chery", modelo="Arrizo", segmento="Sedán B",
        claim="Repuestos accesibles y precio competitivo",
        ventas="1.534 unidades en 2025",
        datos=[("$16.000", "precio desde", ACC2), ("+50,1%", "Chery en 2026", MORADO),
               ("$145", "costo al mes", ACC), ("Sedán", "segmento", MUT)],
        nota="La marca china que más creció en el segmento"),
}


def ficha_modelo(slug, d):
    fig, ax = lona()
    cabecera(fig, ax, f"Análisis · {d['marca']}")

    # marca y modelo
    fig.text(0.035, 0.855, d["marca"].upper(), color=DIM, fontsize=13,
             fontweight="bold", va="top", ha="left")
    fig.text(0.035, 0.815, d["modelo"], color=TX, fontsize=40,
             fontweight="bold", va="top", ha="left")
    fig.text(0.035, 0.700, f"{d['segmento']}  ·  {d['ventas']}",
             color=ACC, fontsize=14, va="top", ha="left")

    # claim
    bloque(ax, 3, 50, 94, 11, CARD)
    fig.text(0.5, 0.615, d["claim"], color=TX, fontsize=14,
             va="top", ha="center", style="italic", zorder=6)

    # cuatro datos
    x0, ancho, gap = 3, 22.0, 2.0
    for i, (val, lab, col) in enumerate(d["datos"]):
        dato(ax, x0 + i * (ancho + gap), 22, ancho, 22, val, lab, col)

    pie(fig, f"Fuente: SRI, ANT, AEADE y tarifarios de concesionarios. {d['nota']}. Valores referenciales.")
    return guardar(fig, f"ficha-{slug}.png")


# ============================================================ TRAMITES
TRAMITES = {
    "matricula-vehicular-ecuador-2026-costos-requisitos": dict(
        etiqueta="Trámite", titulo="Matrícula vehicular", sub="Cinco rubros, un solo pago anual",
        datos=[("$180", "promedio al año", ACC), ("$35", "desde, auto económico", ACC2),
               ("$1.800+", "SUV de lujo", ROJO), ("5", "rubros que la componen", MUT)],
        nota="Incluye IPVM del SRI, rodaje municipal, SPPAT, tasa ANT y revisión técnica"),

    "como-hacer-traspaso-dominio-vehiculo-ecuador": dict(
        etiqueta="Trámite", titulo="Traspaso de dominio", sub="Cuatro pasos, del notario al registro",
        datos=[("1%", "impuesto del valor", ACC), ("$10", "servicio GAD", ACC2),
               ("$25", "especie de matrícula", ACC2), ("4", "pasos del proceso", MUT)],
        nota="El impuesto se calcula sobre el mayor entre el contrato y el avalúo del SRI"),

    "revision-tecnica-vehicular-ecuador-guia": dict(
        etiqueta="Trámite", titulo="Revisión técnica", sub="Cuándo, dónde y cuánto cuesta",
        datos=[("$35", "vehículos livianos", ACC), ("$50", "vehículos pesados", ROJO),
               ("$27", "taxis", ACC2), ("$8", "adhesivo adicional", MUT)],
        nota="El rechequeo es gratuito dentro del plazo. La tercera revisión cuesta la mitad"),

    "certificado-unico-vehicular-cuv-ecuador": dict(
        etiqueta="Trámite", titulo="Certificado único vehicular", sub="El historial completo de tu auto",
        datos=[("$7,50", "costo del trámite", ACC), ("CUV", "sigla oficial", MUT),
               ("En línea", "o presencial", ACC2), ("Sin caducidad", "mientras no cambie", ACC2)],
        nota="Contiene características técnicas, gravámenes e historial del vehículo"),

    "impuesto-compraventa-vehiculos-usados-ecuador": dict(
        etiqueta="Trámite", titulo="Impuesto del 1%", sub="Por compraventa de vehículos usados",
        datos=[("1%", "sobre el mayor valor", ACC), ("$120", "ejemplo: auto de $12.000", ACC2),
               ("$300", "ejemplo: auto de $30.000", ACC2), ("Contrato o avalúo", "la base", MUT)],
        nota="Se paga en institución financiera autorizada antes del cambio de propietario"),
}


def ficha_tramite(slug, d):
    fig, ax = lona()
    cabecera(fig, ax, d["etiqueta"], AZUL)

    fig.text(0.035, 0.820, d["titulo"], color=TX, fontsize=34,
             fontweight="bold", va="top", ha="left")
    fig.text(0.035, 0.700, d["sub"], color=AZUL, fontsize=15,
             va="top", ha="left")

    x0, ancho, gap = 3, 22.0, 2.0
    for i, (val, lab, col) in enumerate(d["datos"]):
        dato(ax, x0 + i * (ancho + gap), 22, ancho, 24, val, lab, col)

    pie(fig, f"Fuente: SRI, ANT y GAD municipales. {d['nota']}. Verifica el valor de tu cantón.")
    return guardar(fig, f"ficha-{slug}.png")


# ============================================================ ELECTRICOS
ELECTRICOS = {
    "carros-electricos-ecuador-catalogo-precios-2026": dict(
        titulo="Carros eléctricos en Ecuador", sub="Catálogo, precios y autonomía real",
        datos=[("23", "marcas disponibles", ACC), ("42", "modelos a la venta", ACC2),
               ("$28.000", "precio más bajo", ACC2), ("$150.000", "precio más alto", ROJO)],
        nota="Autonomía declarada entre 500 y 650 km en los modelos de gama alta"),

    "costo-por-kilometro-electrico-vs-gasolina-ecuador": dict(
        titulo="Eléctrico vs gasolina", sub="Costo por kilómetro recorrido",
        datos=[("$0,05", "tarifa por kWh (baja)", ACC2), ("$0,10", "tarifa por kWh (alta)", ACC),
               ("$8-10", "costo por carga", ACC2), ("$3,26", "galón de Extra", ROJO)],
        nota="Cargar en casa con tarifa nocturna es la forma más económica de mover un auto"),

    "incentivos-tributarios-vehiculos-electricos-ecuador": dict(
        titulo="Incentivos tributarios", sub="Para eléctricos e híbridos",
        datos=[("Exención", "de ciertos impuestos", ACC2), ("ICE", "exento en eléctricos", ACC2),
               ("18%", "del mercado electrificado", ACC), ("3%", "eléctricos puros", MUT)],
        nota="El detalle exacto varía por modelo y debe verificarse con el SRI"),

    "red-carga-electrolineras-ecuador-donde-cargar": dict(
        titulo="Red de carga en Ecuador", sub="Dónde, cuánto y cuánto tarda",
        datos=[("94", "puntos de recarga", ACC), ("48", "en Quito", ACC2),
               ("11", "en Guayaquil", ACC2), ("40 min", "carga rápida mínima", ACC)],
        nota="Carga en casa con 220 V toma alrededor de 8 horas. Carga rápida: 40 min a 1,5 h"),

    "hibrido-vs-electrico-vs-gasolina-ecuador-que-conviene": dict(
        titulo="Híbrido vs eléctrico vs gasolina", sub="Cuál conviene según tu uso",
        datos=[("Ciudad", "el eléctrico gana", ACC2), ("Carretera", "el híbrido compite", ACC2),
               ("Sin cargador", "la gasolina sigue", ROJO), ("18%", "del mercado ya es eléctrico", ACC)],
        nota="La respuesta depende de kilometraje, acceso a cargador y presupuesto, no de moda"),
}


def ficha_electrico(slug, d):
    fig, ax = lona()
    cabecera(fig, ax, "Eléctricos e híbridos", ACC2)

    fig.text(0.035, 0.820, d["titulo"], color=TX, fontsize=32,
             fontweight="bold", va="top", ha="left")
    fig.text(0.035, 0.710, d["sub"], color=ACC2, fontsize=15,
             va="top", ha="left")

    x0, ancho, gap = 3, 22.0, 2.0
    for i, (val, lab, col) in enumerate(d["datos"]):
        dato(ax, x0 + i * (ancho + gap), 22, ancho, 24, val, lab, col)

    pie(fig, f"Fuente: AEADE, SRI y operadores de red de carga. {d['nota']}.")
    return guardar(fig, f"ficha-{slug}.png")


# ============================================================ GENERICAS
GENERICAS = {
    "top-10-cuanto-cuesta-mantener-auto-ecuador": dict(
        etiqueta="Costos", titulo="Cuánto cuesta mantener cada auto",
        sub="Top 10 modelos más vendidos de Ecuador",
        datos=[("$120", "el más económico", ACC2), ("$430", "el más caro", ROJO),
               ("$310", "diferencia mensual", ACC), ("12.000 km", "al año, supuesto", MUT)],
        nota="Incluye combustible, seguro, mantenimiento y matrícula"),

    "cambio-de-aceite-ecuador-cada-cuantos-km-cuanto-cuesta": dict(
        etiqueta="Mantenimiento", titulo="Cambio de aceite",
        sub="Cada cuántos km y cuánto cuesta",
        datos=[("$50-90", "costo por servicio", ACC), ("15.000 km", "aceite sintético", ACC2),
               ("10.000 km", "semisintético", ACC2), ("7.000 km", "mineral", MUT)],
        nota="En Quito, Guayaquil y la sierra conviene revisar con mayor frecuencia"),

    "costos-mantenimiento-por-marca-ecuador": dict(
        etiqueta="Costos", titulo="Mantenimiento por marca",
        sub="Cuánto cuesta al año cada fabricante",
        datos=[("$300", "Nissan, el más bajo", ACC2), ("$600", "Toyota", ACC2),
               ("$1.200", "RAM, el más alto", ROJO), ("$3.500", "diferencia a 5 años", ACC)],
        nota="La brecha entre la marca más económica y la más cara se acumula con los años"),

    "mejor-carro-comprar-ecuador-2026-por-presupuesto": dict(
        etiqueta="Compra", titulo="Mejor carro por presupuesto",
        sub="Guía 2026 por rangos de precio",
        datos=[("$14.000", "rango de entrada", ACC2), ("$22.000", "rango medio", ACC),
               ("$35.000+", "rango alto", ROJO), ("124.505", "autos vendidos en 2025", MUT)],
        nota="El mercado creció 41,4% en el primer semestre de 2026, récord histórico"),

    "que-revisar-comprar-carro-usado-ecuador": dict(
        etiqueta="Compra", titulo="Qué revisar en un usado",
        sub="Checklist antes de pagar",
        datos=[("Documentos", "primero, siempre", ACC2), ("Improntas", "motor y chasis", ACC),
               ("Gravámenes", "consultar antes", ROJO), ("Prueba", "en frío y en caliente", ACC2)],
        nota="Un usado con gravamen vigente no se puede transferir hasta que se cancele"),

    "verificar-gravamenes-multas-carro-usado-ecuador": dict(
        etiqueta="Compra", titulo="Gravámenes y multas",
        sub="Cómo verificar antes de comprar",
        datos=[("CUV", "el documento clave", ACC), ("$7,50", "costo del CUV", ACC2),
               ("ANT", "donde consultar", ACC2), ("Riesgo", "sin verificar", ROJO)],
        nota="El Certificado Único Vehicular revela gravámenes, restricciones e historial"),

    "precio-justo-carro-usado-ecuador-como-calcularlo": dict(
        etiqueta="Compra", titulo="Precio justo de un usado",
        sub="Cómo calcularlo antes de negociar",
        datos=[("Avalúo", "del SRI, la base", ACC), ("1%", "impuesto de venta", ACC2),
               ("20%/año", "depreciación del avalúo", ACC2), ("Negociar", "con datos", MUT)],
        nota="El avalúo del SRI no siempre coincide con el valor de mercado del vehículo"),

    "kia-soluto-vs-chevrolet-groove-ecuador": dict(
        etiqueta="Comparativa", titulo="Kia Soluto vs Chevrolet Groove",
        sub="El sedán más vendido contra el SUV más vendido",
        datos=[("$15.799", "Soluto desde", ACC2), ("$19.999", "Groove desde", ACC),
               ("15,5 km/l", "Soluto consume", ACC2), ("14,0 km/l", "Groove consume", ACC)],
        nota="El Soluto gana en costo; el Groove en espacio y posición de manejo"),

    "kia-sonet-vs-hyundai-creta-ecuador": dict(
        etiqueta="Comparativa", titulo="Kia Sonet vs Hyundai Creta",
        sub="Dos SUV, dos segmentos distintos",
        datos=[("$21.599", "Sonet desde", ACC2), ("Sonet", "subcompacto", MUT),
               ("Creta", "SUV mediano", MUT), ("6 airbags", "Sonet de serie", ACC2)],
        nota="Ambos ensamblados en Ecuador: repuestos locales y entregas más rápidas"),

    "camionetas-4x4-ecuador-dmax-poer-hilux": dict(
        etiqueta="Comparativa", titulo="D-Max vs Poer vs Hilux",
        sub="Las tres camionetas más vendidas de Ecuador",
        datos=[("5.515", "D-Max, la líder", ACC), ("$27.000", "Poer, la más barata", ACC2),
               ("Toyota", "mayor reventa", ACC2), ("Ambato", "donde se ensambla la Poer", MUT)],
        nota="Las tres tienen uso de trabajo; cambian precio, repuestos y valor de reventa"),

    "top-10-cuanto-cuesta-mantener-auto-ecuador-alt": None,
}


def ficha_generica(slug, d):
    fig, ax = lona()
    cabecera(fig, ax, d["etiqueta"], ACC)

    fig.text(0.035, 0.820, d["titulo"], color=TX, fontsize=33,
             fontweight="bold", va="top", ha="left")
    fig.text(0.035, 0.705, d["sub"], color=ACC, fontsize=15,
             va="top", ha="left")

    x0, ancho, gap = 3, 22.0, 2.0
    for i, (val, lab, col) in enumerate(d["datos"]):
        dato(ax, x0 + i * (ancho + gap), 22, ancho, 24, val, lab, col)

    pie(fig, f"Fuente: SRI, ANT, AEADE y tarifarios publicados. {d['nota']}. Valores referenciales.")
    return guardar(fig, f"ficha-{slug}.png")


# ============================================================ MAIN
def main():
    generadas = []
    faltantes = []

    for slug, d in MODELOS.items():
        # los articulos de modelos usan el sufijo -analisis-completo-ecuador
        generadas.append(ficha_modelo(f"{slug}-analisis-completo-ecuador", d))
    for slug, d in TRAMITES.items():
        generadas.append(ficha_tramite(slug, d))
    for slug, d in ELECTRICOS.items():
        generadas.append(ficha_electrico(slug, d))
    for slug, d in GENERICAS.items():
        if d is None:
            continue
        generadas.append(ficha_generica(slug, d))

    print(f"fichas generadas: {len(generadas)}")

    # que articulos del content no tienen ficha?
    slugs = {os.path.basename(f)[:-3] for f in glob.glob(f"{BASE}/content/*.md")}
    con_ficha = set()
    for g in generadas:
        n = os.path.basename(g)
        if n.startswith("ficha-"):
            con_ficha.add(n[6:-4])

    for s in sorted(slugs - con_ficha):
        faltantes.append(s)
        print(f"  SIN FICHA: {s}")

    print(f"\ntotal imagenes en dist/img: {len(os.listdir(OUT))}")
    return generadas, faltantes


if __name__ == "__main__":
    main()
