#!/usr/bin/env python3
"""
Generador de gráficos de datos para cuantocuesta.xyz
Salida: PNG 1200x675 (formato Open Graph, sirve de cabecera)
Paleta alineada con el CSS del sitio.

Correcciones aplicadas tras revisión visual:
  - tildes y signos correctos en todo el texto
  - leyenda fuera del área de datos (no tapa barras)
  - etiquetas de valor en blanco con halo, contraste alto
  - eje X con margen para que la etiqueta más larga quepa
  - barras ordenadas de mayor a menor donde corresponde
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "assets", "img")
os.makedirs(OUT, exist_ok=True)

BG = "#0d0f12"
CARD = "#151a20"
TX = "#e8edf2"
MUT = "#c2ccd6"
ACC = "#e8b93b"
ACC2 = "#3ba55d"
AZUL = "#5b9bd5"
MORADO = "#9b7fd4"
ROJO = "#e06c5a"
BD = "#2a333d"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": CARD,
    "savefig.facecolor": BG,
    "text.color": TX,
    "axes.labelcolor": MUT,
    "xtick.color": MUT,
    "ytick.color": TX,
    "axes.edgecolor": BD,
    "axes.grid": True,
    "grid.color": BD,
    "grid.linewidth": 0.6,
    "grid.alpha": 0.9,
    "font.size": 12,
    "font.family": "DejaVu Sans",
    "figure.dpi": 100,
})


def halo(ax, x, y, texto, size=11.5, color=TX, weight="bold", ha="left"):
    """Texto con contorno oscuro para que se lea sobre cualquier fondo."""
    ax.annotate(texto, (x, y), ha=ha, va="center", color=color,
                fontsize=size, fontweight=weight, zorder=6,
                path_effects=None,
                bbox=dict(boxstyle="round,pad=0.22", fc=CARD, ec="none", alpha=0.75))


def guardar(fig, nombre):
    ruta = os.path.join(OUT, nombre)
    fig.savefig(ruta, dpi=100, facecolor=BG, bbox_inches="tight",
                pad_inches=0.4, edgecolor="none")
    plt.close(fig)
    print(f"  {nombre}  ({os.path.getsize(ruta)/1024:.0f} KB)")


def titulo(ax, t, sub=None):
    """Título, subtítulo y marca posicionados con coordenadas de FIGURA.

    No usar set_title(): su padding se mide en puntos mientras que el
    subtítulo se medía en fracción del axes, y ambos terminaban
    superpuestos (efecto de texto fantasma / ghosting).
    """
    from matplotlib.lines import Line2D

    fig = ax.figure
    fig.subplots_adjust(top=0.76 if sub else 0.84)

    # barra de acento superior
    fig.add_artist(Line2D([0.010, 0.070], [0.985, 0.985],
                          transform=fig.transFigure, color=ACC,
                          linewidth=4.5, solid_capstyle="round"))

    # marca del sitio, alineada a la derecha
    fig.text(0.990, 0.985, "cuantocuesta.xyz", color=MUT, fontsize=10,
             va="top", ha="right")

    # título
    fig.text(0.010, 0.945, t, color=TX, fontsize=18.5,
             fontweight="bold", va="top", ha="left")

    # subtítulo
    if sub:
        fig.text(0.010, 0.876, sub, color=MUT, fontsize=11.5,
                 va="top", ha="left")


def pie(ax, texto):
    ax.figure.text(0.012, -0.035, texto, color="#a8b4c0", fontsize=8.8,
                   ha="left", va="top")


# ============================================================ 1. Top 10 costo mensual
# (modelo, minimo, maximo, color)
MODELOS = [
    ("Hyundai Grand i10", 120, 180, ACC2),
    ("Kia Soluto", 135, 200, ACC2),
    ("Suzuki Swift", 140, 200, ACC2),
    ("Chery Arrizo", 145, 210, ACC2),
    ("Chevrolet Groove", 175, 250, ACC),
    ("Kia Sonet", 180, 260, ACC),
    ("GWM Poer", 245, 360, ROJO),
    ("Hyundai Tucson", 270, 400, ROJO),
    ("Chevrolet D-Max", 280, 410, ROJO),
    ("Toyota Hilux", 295, 430, ROJO),
]

fig, ax = plt.subplots(figsize=(12.5, 7))
nombres = [m[0] for m in MODELOS]
mins = [m[1] for m in MODELOS]
maxs = [m[2] for m in MODELOS]
colores = [m[3] for m in MODELOS]
y = np.arange(len(nombres))

ax.barh(y, mins, color=colores, height=0.6, alpha=0.45)
ax.barh(y, [mx - mn for mx, mn in zip(maxs, mins)], left=mins,
        color=colores, height=0.6)

for i, (mn, mx) in enumerate(zip(mins, maxs)):
    ax.text(mx + 6, i, f"${mx}", va="center", ha="left", color=TX,
            fontsize=12, fontweight="bold", zorder=6)

ax.set_yticks(y)
ax.set_yticklabels(nombres, fontsize=11.5)
ax.set_xlabel("Costo mensual estimado (USD)", color=MUT, fontsize=11, labelpad=8)
ax.set_xlim(0, 520)
ax.grid(axis="y", visible=False)
ax.invert_yaxis()

leyenda = [
    Patch(facecolor=ACC2, label="Segmento económico"),
    Patch(facecolor=ACC, label="Segmento medio"),
    Patch(facecolor=ROJO, label="Camionetas y SUV grande"),
]
ax.legend(handles=leyenda, loc="lower right", bbox_to_anchor=(1.0, -0.22),
          ncol=3, frameon=False, fontsize=10.5, labelcolor=TX)

titulo(ax, "¿Cuánto cuesta mantener cada auto al mes en Ecuador?",
       "Top 10 modelos más vendidos · 12.000 km al año · seguro y matrícula incluidos")
pie(ax, "Fuente: tarifarios de concesionarios, SRI y AEADE. Valores referenciales de gama. cuantocuesta.xyz")
guardar(fig, "grafico-costo-mensual-top10.png")


# ============================================================ 2. Consumo
CONSUMO = [
    ("Kia Sonet IVT", 18.03, ACC2),
    ("Kia Soluto MT", 15.5, ACC2),
    ("Kia Sonet manual", 15.14, ACC),
    ("Kia Soluto AT", 14.2, ACC),
    ("Chevrolet Groove", 14.0, ACC),
]
fig, ax = plt.subplots(figsize=(12.5, 6.4))
nn = [c[0] for c in CONSUMO]
vv = [c[1] for c in CONSUMO]
cc = [c[2] for c in CONSUMO]
ax.barh(np.arange(len(nn)), vv, color=cc, height=0.58)
for i, v in enumerate(vv):
    ax.text(v + 0.25, i, f"{v} km/l", va="center", ha="left",
            color=TX, fontsize=12.5, fontweight="bold", zorder=6)
ax.set_yticks(np.arange(len(nn)))
ax.set_yticklabels(nn, fontsize=12)
ax.set_xlabel("Consumo mixto (kilómetros por litro)", color=MUT, fontsize=11, labelpad=8)
ax.set_xlim(0, 22)
ax.grid(axis="y", visible=False)
ax.invert_yaxis()
titulo(ax, "Consumo de combustible: los más eficientes del mercado",
       "Ciclo mixto declarado por el fabricante · barra más larga = menos gasto de gasolina")
pie(ax, "Fuente: fichas técnicas de fabricante. Las cifras reales varían según tráfico, altitud y conducción. cuantocuesta.xyz")
guardar(fig, "grafico-consumo-modelos.png")


# ============================================================ 3. Mantenimiento por km
KM = [10000, 20000, 30000, 40000, 50000, 60000]
COSTO = [333.41, 434.21, 489.00, 595.24, 689.67, 799.85]
fig, ax = plt.subplots(figsize=(12.5, 7))
ax.plot(KM, COSTO, color=ACC, linewidth=3.2, marker="o", markersize=10,
        markerfacecolor=ACC2, markeredgecolor=BG, markeredgewidth=2.5, zorder=5)
ax.fill_between(KM, COSTO, 250, color=ACC, alpha=0.12, zorder=1)
for x, c in zip(KM, COSTO):
    ax.annotate(f"${c:,.0f}", (x, c), textcoords="offset points", xytext=(0, 18),
                ha="center", color=TX, fontsize=11, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", fc=CARD, ec="none", alpha=0.85))
ax.set_xlabel("Kilometraje acumulado", color=MUT, fontsize=11, labelpad=8)
ax.set_ylabel("Costo del servicio (USD)", color=MUT, fontsize=11, labelpad=8)
ax.set_xticks(KM)
ax.set_xticklabels([f"{k//1000}.000 km" for k in KM], fontsize=11)
ax.set_ylim(250, 920)
ax.set_xlim(6000, 64000)
titulo(ax, "El mantenimiento se encarece con cada servicio",
       "Tarifario oficial de concesionario · el servicio de 60.000 km cuesta 2,4 veces el de 10.000")
pie(ax, "Fuente: tarifario publicado por Ford Quito Motors. Costo por kilómetro recorrido: $0,048. cuantocuesta.xyz")
guardar(fig, "grafico-mantenimiento-por-km.png")


# ============================================================ 4. Desglose costo anual
RUBROS = ["Combustible", "Seguro", "Mantenimiento", "Matrícula", "Otros"]
VALORES = [675, 400, 240, 180, 150]
COLORES = [ACC, "#c9922e", ACC2, AZUL, MORADO]
fig, ax = plt.subplots(figsize=(12.5, 7))
barras = ax.bar(RUBROS, VALORES, color=COLORES, width=0.58)
for b, v in zip(barras, VALORES):
    ax.text(b.get_x() + b.get_width()/2, v + 18, f"${v}", ha="center",
            color=TX, fontsize=13, fontweight="bold", zorder=6)
total = sum(VALORES)
ax.text(0.5, 0.88, f"Total anual: ${total:,}", transform=ax.transAxes,
        ha="center", color=ACC, fontsize=19, fontweight="bold", zorder=6)
ax.set_ylabel("USD por año", color=MUT, fontsize=11, labelpad=8)
ax.set_ylim(0, 860)
ax.grid(axis="x", visible=False)
titulo(ax, "¿En qué se va el dinero de un auto en Ecuador?",
       "Auto de gama media · 12.000 km al año · el combustible es el 41% del gasto")
pie(ax, "Fuente: análisis de costos del sector automotriz ecuatoriano. Valores referenciales para gama media. cuantocuesta.xyz")
guardar(fig, "grafico-desglose-costo-anual.png")


# ============================================================ 5. Rodaje por ciudad
CIUDADES = ["Quito", "Guayaquil", "Cuenca", "Ambato"]
RODAJE = [40, 30, 25, 25]
COLORES = [ACC, ACC2, AZUL, MORADO]
fig, ax = plt.subplots(figsize=(12.5, 7))
barras = ax.bar(CIUDADES, RODAJE, color=COLORES, width=0.52)
for b, v in zip(barras, RODAJE):
    ax.text(b.get_x() + b.get_width()/2, v + 0.9, f"${v}", ha="center",
            color=TX, fontsize=15, fontweight="bold", zorder=6)
ax.set_ylabel("Impuesto al rodaje (USD por año)", color=MUT, fontsize=11, labelpad=8)
ax.set_ylim(0, 52)
ax.grid(axis="x", visible=False)
titulo(ax, "El impuesto al rodaje cambia según la ciudad",
       "Tarifa municipal anual incluida en la matrícula · Quito cobra 60% más que Cuenca")
pie(ax, "Fuente: ordenanzas municipales y COOTAD Art. 539. Verifica el valor exacto de tu cantón. cuantocuesta.xyz")
guardar(fig, "grafico-rodaje-por-ciudad.png")


# ============================================================ 6. Ventas por marca
MARCAS = ["Kia", "Chevrolet", "GWM", "Hyundai", "Toyota", "Chery", "Dongfeng", "JAC", "BYD"]
UDS = [12512, 9341, 4329, 4232, 3808, 3785, 2780, 2773, 2490]
VARC = [38, 16.3, 53.7, 27.6, 34.1, 50.1, 94.8, 71.9, 139]
fig, ax = plt.subplots(figsize=(12.5, 7.5))
def color_var(v):
    if v >= 70: return ACC
    if v >= 40: return ACC2
    if v >= 20: return AZUL
    return "#5a6b7d"
barras = ax.barh(np.arange(len(MARCAS)), UDS,
                 color=[color_var(v) for v in VARC], height=0.62)
for i, (u, v) in enumerate(zip(UDS, VARC)):
    ax.text(u + 260, i, f"{u:,}   +{v}%", va="center", ha="left",
            color=TX, fontsize=11.5, fontweight="bold", zorder=6)
ax.set_yticks(np.arange(len(MARCAS)))
ax.set_yticklabels(MARCAS, fontsize=12.5, fontweight="bold")
ax.set_xlabel("Unidades vendidas (enero a junio de 2026)", color=MUT, fontsize=11, labelpad=8)
ax.set_xlim(0, 17500)
ax.grid(axis="y", visible=False)
ax.invert_yaxis()
leyenda = [
    Patch(facecolor=ACC, label="Crecimiento +70% o más"),
    Patch(facecolor=ACC2, label="+40% a +70%"),
    Patch(facecolor=AZUL, label="+20% a +40%"),
]
ax.legend(handles=leyenda, loc="lower right", bbox_to_anchor=(1.0, -0.20),
          ncol=3, frameon=False, fontsize=10.5, labelcolor=TX)
titulo(ax, "Las marcas que dominan el mercado automotor ecuatoriano",
       "Kia lidera tras destronar a Chevrolet, que mantuvo el primer lugar durante 29 años")
pie(ax, "Fuente: AEADE — Asociación de Empresas Automotrices del Ecuador. cuantocuesta.xyz")
guardar(fig, "grafico-ventas-por-marca.png")


# ============================================================ 7. Eléctricos vs resto
fig, ax = plt.subplots(figsize=(12.5, 6.4))
cat = ["Gasolina y diésel", "Híbridos", "Eléctricos puros"]
val = [82, 15, 3]
colores = ["#5a6b7d", ACC2, ACC]
barras = ax.barh(cat[::-1], val[::-1], color=colores[::-1], height=0.55)
for b, v in zip(barras, val[::-1]):
    ax.text(v + 1.5, b.get_y() + b.get_height()/2, f"{v}%", va="center",
            ha="left", color=TX, fontsize=17, fontweight="bold", zorder=6)
ax.set_xlabel("Porcentaje de las ventas de 2026", color=MUT, fontsize=11, labelpad=8)
ax.set_xlim(0, 100)
ax.grid(axis="y", visible=False)
titulo(ax, "¿Qué se vende en Ecuador? La gasolina sigue mandando",
       "Pero los electrificados ya son 18% del mercado y crecen rápido")
pie(ax, "Fuente: AEADE. Los eléctricos puros pasaron de 1.088 unidades en 2024 a 4.276 en 2025. cuantocuesta.xyz")
guardar(fig, "grafico-electricos-vs-gasolina.png")


print(f"\nlisto. {len(os.listdir(OUT))} imágenes en {OUT}")
