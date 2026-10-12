#!/usr/bin/env python3
"""
Generador de sitio estático, Portal automotriz Ecuador.
Sin dependencias externas. Solo stdlib.

Uso:
    python3 build.py

Salida: dist/
"""
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import date
from html import escape
from pathlib import Path

import anuncios

BASE = Path(__file__).parent
DIST = BASE / "dist"
DATA = BASE / "data"
CONTENT = BASE / "content"
ASSETS = BASE / "assets"

SITIO = {
    "nombre": "Autos Ecuador",
    "tagline": "Costos, trámites y comparativas reales de autos en Ecuador",
    "descripcion": "Guías de costos de mantenimiento, trámites vehiculares y "
                   "comparativas de los autos más vendidos en Ecuador. Datos "
                   "actualizados de fuentes oficiales.",
    "url": "https://cuantocuesta.xyz",
    "idioma": "es-EC",
    "anio": date.today().year,
    "actualizado": date.today().isoformat(),
}


# ---------------------------------------------------------------- utilidades
def slugify(texto):
    t = unicodedata.normalize("NFKD", texto)
    t = t.encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_contenido():
    """Lee los artículos en Markdown de content/."""
    articulos = []
    if not CONTENT.exists():
        return articulos
    for p in sorted(CONTENT.glob("*.md")):
        texto = p.read_text(encoding="utf-8")
        meta, cuerpo = {}, texto
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
        if m:
            for linea in m.group(1).splitlines():
                if ":" in linea:
                    k, v = linea.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            cuerpo = m.group(2).strip()
        meta.setdefault("titulo", p.stem)
        meta.setdefault("slug", p.stem)
        meta.setdefault("categoria", "general")
        meta.setdefault("descripcion", "")
        meta["cuerpo_md"] = cuerpo
        articulos.append(meta)
    return articulos


def md_a_html(md):
    """Markdown mínimo: h2, h3, listas, tablas, negritas, párrafos, links."""
    lineas = md.split("\n")
    out, en_ul, en_ol, en_tabla = [], False, False, False
    i = 0

    def cerrar():
        nonlocal en_ul, en_ol, en_tabla
        if en_ul:
            out.append("</ul>"); en_ul = False
        if en_ol:
            out.append("</ol>"); en_ol = False
        if en_tabla:
            out.append("</tbody></table></div>"); en_tabla = False

    while i < len(lineas):
        ln = lineas[i].rstrip()
        if not ln.strip():
            cerrar(); i += 1; continue

        # tabla
        if ln.startswith("|") and i + 1 < len(lineas) and re.match(r"^\|[\s:\-|]+\|$", lineas[i + 1].strip()):
            cerrar()
            cab = [c.strip() for c in ln.strip("|").split("|")]
            out.append('<div class="tabla-wrap"><table><thead><tr>')
            for c in cab:
                out.append(f"<th>{escape(c)}</th>")
            out.append("</tr></thead><tbody>")
            en_tabla = True
            i += 2
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                celdas = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in celdas) + "</tr>")
                i += 1
            cerrar(); continue

        if ln.startswith("### "):
            cerrar(); out.append(f"<h3>{inline(ln[4:])}</h3>")
        elif ln.startswith("## "):
            cerrar(); out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("# "):
            cerrar(); out.append(f"<h2>{inline(ln[2:])}</h2>")
        elif re.match(r"^[-*] ", ln):
            if not en_ul:
                cerrar(); out.append("<ul>"); en_ul = True
            out.append(f"<li>{inline(ln[2:])}</li>")
        elif re.match(r"^\d+\. ", ln):
            if not en_ol:
                cerrar(); out.append("<ol>"); en_ol = True
            out.append(f"<li>{inline(re.sub(r'^\d+\. ', '', ln))}</li>")
        elif ln.startswith("> "):
            cerrar(); out.append(f"<blockquote>{inline(ln[2:])}</blockquote>")
        elif ln.startswith("---"):
            cerrar(); out.append("<hr>")
        else:
            cerrar(); out.append(f"<p>{inline(ln)}</p>")
        i += 1
    cerrar()
    return "\n".join(out)


def inline(t):
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', t)
    return t


# ---------------------------------------------------------------- plantillas
CSS = """
:root{--bg:#0d0f12;--card:#151a20;--tx:#e8edf2;--mut:#8d99a6;--acc:#e8b93b;--acc2:#3ba55d;--bd:#232b33}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--tx);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
-webkit-font-smoothing:antialiased}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:820px;margin:0 auto;padding:0 18px}
header{background:linear-gradient(180deg,#151a20,#0d0f12);border-bottom:1px solid var(--bd);padding:14px 0;position:sticky;top:0;z-index:9}
.hrow{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
.logo{font-weight:800;font-size:1.15rem;letter-spacing:-.4px;color:var(--tx)}
.logo span{color:var(--acc)}
nav a{color:var(--mut);font-size:.86rem;margin-left:15px;font-weight:500}
nav a:hover{color:var(--acc)}
main{padding:26px 0 60px}
h1{font-size:1.85rem;line-height:1.22;letter-spacing:-.6px;margin-bottom:12px;font-weight:800}
h2{font-size:1.3rem;margin:30px 0 11px;letter-spacing:-.3px;font-weight:700;padding-top:6px}
h3{font-size:1.06rem;margin:22px 0 8px;font-weight:700;color:#cdd6e0}
p{margin:11px 0}
ul,ol{margin:11px 0 11px 22px}
li{margin:6px 0}
hr{border:0;border-top:1px solid var(--bd);margin:26px 0}
blockquote{border-left:3px solid var(--acc);background:#151a20;padding:12px 16px;margin:16px 0;color:#c3ccd6;border-radius:0 8px 8px 0}
code{background:#1e242c;padding:2px 6px;border-radius:4px;font-size:.88em;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.lead{color:var(--mut);font-size:1.02rem;margin-bottom:22px}
.meta{color:var(--mut);font-size:.8rem;margin-bottom:22px;padding-bottom:16px;border-bottom:1px solid var(--bd)}
.tabla-wrap{overflow-x:auto;margin:18px 0;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:.9rem;min-width:440px}
th{background:#1c232b;text-align:left;padding:10px 12px;font-weight:700;border-bottom:2px solid var(--bd);white-space:nowrap}
td{padding:9px 12px;border-bottom:1px solid var(--bd)}
tr:hover td{background:#171d24}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin:22px 0}
.card{background:var(--card);border:1px solid var(--bd);border-radius:11px;padding:17px;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--acc);transform:translateY(-2px)}
.card h3{margin:0 0 7px;font-size:1rem;color:var(--tx)}
.card p{color:var(--mut);font-size:.86rem;margin:0}
.tag{display:inline-block;background:#1e252d;color:var(--acc);font-size:.7rem;padding:3px 9px;border-radius:11px;
font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:9px}
.destacado{background:linear-gradient(135deg,#1a2028,#151a20);border:1px solid var(--bd);border-left:3px solid var(--acc);
border-radius:9px;padding:16px 18px;margin:20px 0}
.destacado h3{margin-top:0}
.figura{margin:0 0 24px;padding:0}
.figura img{width:100%;height:auto;border-radius:11px;border:1px solid var(--bd);display:block}
figcaption{color:var(--mut);font-size:.78rem;margin-top:8px;text-align:center}
footer{border-top:1px solid var(--bd);padding:26px 0;color:var(--mut);font-size:.82rem}
footer a{color:var(--mut)}
.volver{color:var(--mut);font-size:.85rem;display:inline-block;margin-bottom:16px}
.legal li{margin:4px 0}
.intro-seccion{margin:22px 0 30px}
.intro-seccion p{color:var(--mut);font-size:.95rem;line-height:1.72;margin:0 0 14px}
.intro-seccion strong{color:var(--tx)}
.intro-seccion a{color:#e9b949}
.anuncio{margin:26px 0;padding:14px;background:var(--card);border:1px solid var(--bd);
  border-radius:10px;text-align:center;min-height:110px}
.anuncio-etiq{display:block;color:var(--mut);font-size:.68rem;text-transform:uppercase;
  letter-spacing:.09em;margin-bottom:9px}
.anuncio ins{background:transparent}
.calc{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin:26px 0}
.calc-fila{display:flex;flex-wrap:wrap;align-items:center;gap:14px;padding:11px 0;border-bottom:1px solid var(--bd)}
.calc-fila:last-child{border-bottom:0}
.calc-fila > label{flex:0 0 210px;color:var(--tx);font-size:.92rem}
.calc select,.calc input[type=number]{background:#0e1116;color:var(--tx);border:1px solid var(--bd);
  border-radius:7px;padding:9px 12px;font-size:.95rem;font-family:inherit;min-width:150px}
.calc-radios{display:flex;flex-wrap:wrap;gap:16px}
.calc-radios label{display:flex;align-items:center;gap:7px;color:var(--mut);font-size:.9rem;cursor:pointer}
.calc-res{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:26px 0}
.calc-total{background:linear-gradient(160deg,#171b22,#0f1216);border:1px solid var(--bd);
  border-radius:12px;padding:20px 22px;display:flex;flex-direction:column;gap:7px}
.calc-total .etiqueta{color:var(--mut);font-size:.78rem;text-transform:uppercase;letter-spacing:.07em}
.calc-total span:last-child{font-size:2rem;font-weight:700;color:#e9b949}
.calc-anual span:last-child{color:#7fb3d5;font-size:1.5rem}
.calc-km span:last-child{color:#8bc98b;font-size:1.5rem}
.calc-tabla{width:100%;border-collapse:collapse;margin:20px 0;font-size:.92rem}
.calc-tabla th{text-align:left;color:var(--mut);font-size:.78rem;text-transform:uppercase;
  letter-spacing:.07em;padding:11px 12px;border-bottom:1px solid var(--bd)}
.calc-tabla td{padding:11px 12px;border-bottom:1px solid var(--bd);color:var(--tx)}
.calc-tabla .num{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.calc-tabla .calc-desc{color:var(--mut);font-size:.85rem}
.calc-tabla .calc-sum td{border-top:2px solid var(--acc);border-bottom:0;font-weight:700;
  color:#e9b949;padding-top:14px}
@media(max-width:600px){
 h1{font-size:1.5rem}h2{font-size:1.15rem}
 nav a{margin-left:0;margin-right:14px;display:inline-block}
 table{font-size:.82rem}
 .calc-fila > label{flex:1 1 100%}
 .calc select,.calc input[type=number]{width:100%}
}
"""


def pagina(titulo, descripcion, cuerpo, ruta_rel="", canonical="", og_imagen="", schema=""):
    nav = ('<nav><a href="' + ruta_rel + 'index.html">Inicio</a>'
           '<a href="' + ruta_rel + 'costos.html">Costos</a>'
           '<a href="' + ruta_rel + 'tramites.html">Trámites</a>'
           '<a href="' + ruta_rel + 'vendidos.html">Más vendidos</a>'
           '<a href="' + ruta_rel + 'comparativas.html">Comparativas</a>'
           '<a href="' + ruta_rel + 'compra.html">Comprar usado</a>'
           '<a href="' + ruta_rel + 'electricos.html">Eléctricos</a>'
           '<a href="' + ruta_rel + 'calculadora.html">Calculadora</a></nav>')
    og = f'<meta property="og:image" content="{escape(og_imagen)}">' if og_imagen else ""
    tw = '<meta name="twitter:card" content="summary_large_image">' if og_imagen else ""
    ld = "\n".join(
        f'<script type="application/ld+json">{s}</script>' for s in schema) if schema else ""
    ads_head = anuncios.encabezado()
    return f"""<!DOCTYPE html>
<html lang="es-EC">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(titulo)}</title>
<meta name="description" content="{escape(descripcion)}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{escape(titulo)}">
<meta property="og:description" content="{escape(descripcion)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_EC">
{og}
{tw}
<link rel="canonical" href="{canonical}">
<style>{CSS}</style>
{ads_head}
{ld}
</head>
<body>
<header><div class="wrap hrow">
<div class="logo">Autos<span>Ecuador</span></div>
{nav}
</div></header>
<main><div class="wrap">
{cuerpo}
</div></main>
<footer><div class="wrap">
<p><strong>Autos Ecuador</strong>: {escape(SITIO['tagline'])}</p>
<p style="margin-top:9px">Información referencial basada en fuentes oficiales (SRI, ANT, AEADE) y tarifarios
de concesionarios. Los precios, tasas y requisitos cambian: verifica siempre en la entidad correspondiente
antes de tomar una decisión.</p>
<p style="margin-top:9px">Última actualización del sitio: {SITIO['actualizado']}</p>
<p style="margin-top:12px" class="pie-legal">
<a href="{ruta_rel}acerca.html">Acerca de</a> ·
<a href="{ruta_rel}contacto.html">Contacto</a> ·
<a href="{ruta_rel}privacidad.html">Privacidad</a> ·
<a href="{ruta_rel}cookies.html">Cookies</a>
</p>
</div></footer>
</body>
</html>"""


def _jsonld(obj):
    """Serializa JSON-LD sin escapar acentos."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def schema_articulo(a, img):
    """Article + BreadcrumbList para una guía."""
    url = f"{SITIO['url']}/{a['slug']}.html"
    art = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["titulo"],
        "description": a.get("descripcion", ""),
        "inLanguage": "es-EC",
        "datePublished": a.get("actualizado", SITIO["actualizado"]),
        "dateModified": a.get("actualizado", SITIO["actualizado"]),
        "author": {"@type": "Organization", "name": SITIO["nombre"],
                   "url": SITIO["url"]},
        "publisher": {"@type": "Organization", "name": SITIO["nombre"],
                      "url": SITIO["url"]},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "articleSection": a.get("categoria", "general"),
        "isAccessibleForFree": True,
    }
    if img:
        art["image"] = f"{SITIO['url']}/img/{img}"

    migas = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1,
             "name": "Inicio", "item": f"{SITIO['url']}/"},
            {"@type": "ListItem", "position": 2,
             "name": a.get("categoria", "general").title(),
             "item": f"{SITIO['url']}/{a.get('categoria','')}.html"},
            {"@type": "ListItem", "position": 3,
             "name": a["titulo"], "item": url},
        ],
    }
    return [_jsonld(art), _jsonld(migas)]


def schema_sitio():
    """WebSite + Organization para la portada."""
    web = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITIO["nombre"],
        "url": SITIO["url"],
        "description": SITIO["descripcion"],
        "inLanguage": "es-EC",
        "publisher": {"@type": "Organization", "name": SITIO["nombre"]},
    }
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITIO["nombre"],
        "url": SITIO["url"],
        "description": SITIO["descripcion"],
        "areaServed": {"@type": "Country", "name": "Ecuador"},
        "knowsLanguage": "es-EC",
    }
    return [_jsonld(web), _jsonld(org)]


def schema_coleccion(nombre, desc, categoria):
    """CollectionPage + BreadcrumbList para páginas índice."""
    url = f"{SITIO['url']}/{categoria}.html"
    col = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": nombre,
        "description": desc,
        "url": url,
        "inLanguage": "es-EC",
        "isPartOf": {"@type": "WebSite", "name": SITIO["nombre"],
                     "url": SITIO["url"]},
    }
    migas = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1,
             "name": "Inicio", "item": f"{SITIO['url']}/"},
            {"@type": "ListItem", "position": 2, "name": nombre, "item": url},
        ],
    }
    return [_jsonld(col), _jsonld(migas)]


def construir_home(articulos):
    cats = {}
    for a in articulos:
        cats.setdefault(a["categoria"], []).append(a)

    partes = [f"""<h1>Costos reales de tener un auto en Ecuador</h1>
<p class="lead">Guías con datos verificables sobre cuánto cuesta mantener, tramitar y elegir un vehículo
en Ecuador. Sin estimaciones vagas: tarifas del SRI, la ANT y tarifarios de concesionarios.</p>"""]

    if articulos:
        partes.append(f'<p class="meta">{len(articulos)} guías publicadas · Actualizado {SITIO["actualizado"]}</p>')

    # destacados
    portada = [a for a in articulos if a.get("destacado") == "si"][:3]
    if portada:
        partes.append('<h2>Lo más consultado</h2><div class="grid">')
        for a in portada:
            partes.append(f"""<a class="card" href="{a['slug']}.html">
<span class="tag">{escape(a['categoria'])}</span>
<h3>{escape(a['titulo'])}</h3>
<p>{escape(a['descripcion'][:110])}</p></a>""")
        partes.append("</div>")

    orden_cats = ["costos", "tramites", "comparativas", "compra", "mantenimiento", "financiamiento", "electricos"]
    nombres = {
        "costos": "Cuánto cuesta mantener cada auto",
        "tramites": "Trámites vehiculares paso a paso",
        "comparativas": "Comparativas entre modelos",
        "compra": "Comprar un auto usado",
        "mantenimiento": "Mantenimiento y repuestos",
        "financiamiento": "Crédito y financiamiento",
        "electricos": "Eléctricos e híbridos",
    }
    # Las categorias que tienen pagina propia se enlazan desde el h2.
    # OJO: antes el h2 era solo texto, asi que las paginas de categoria que no
    # estaban en el <nav> (compra.html) quedaban HUERFANAS, 0 enlaces entrantes,
    # y Google las deja en "Crawled - currently not indexed".
    PAGINA_PROPIA = {"costos", "tramites", "comparativas", "compra",
                     "electricos", "vendidos"}

    for c in orden_cats + [k for k in cats if k not in orden_cats]:
        if c not in cats:
            continue
        titulo_cat = escape(nombres.get(c, c.title()))
        encabezado = (
            f'<a href="{c}.html">{titulo_cat}</a>' if c in PAGINA_PROPIA else titulo_cat)
        partes.append(f'<h2 id="{c}">{encabezado}</h2><div class="grid">')
        for a in sorted(cats[c], key=lambda x: x["titulo"]):
            partes.append(f"""<a class="card" href="{a['slug']}.html">
<h3>{escape(a['titulo'])}</h3>
<p>{escape(a['descripcion'][:105])}</p></a>""")
        partes.append("</div>")

    return pagina(
        "Autos Ecuador | Costos, trámites y comparativas de autos",
        SITIO["descripcion"],
        "\n".join(partes),
        canonical=f"{SITIO['url']}/",
        schema=schema_sitio(),)


def resolver_imagen(a):
    """Devuelve el nombre del archivo de imagen que realmente existe.

    Orden: lo declarado en el frontmatter, luego la ficha por slug.
    Ignora referencias rotas en lugar de generar un <img> vacío.
    """
    candidatos = []
    if a.get("imagen"):
        candidatos.append(a["imagen"])
    candidatos.append(f"ficha-{a['slug']}.png")
    for c in candidatos:
        if (ASSETS / "img" / c).exists():
            return c
    return ""


def construir_articulo(a, articulos):
    cuerpo_html = md_a_html(a["cuerpo_md"])
    rel = [x for x in articulos if x["categoria"] == a["categoria"] and x["slug"] != a["slug"]][:5]

    partes = [f'<a class="volver" href="index.html">← Inicio</a>']
    partes.append(f'<span class="tag">{escape(a["categoria"])}</span>')
    partes.append(f'<h1>{escape(a["titulo"])}</h1>')
    if a["descripcion"]:
        partes.append(f'<p class="lead">{escape(a["descripcion"])}</p>')
    partes.append(f'<p class="meta">Actualizado: {a.get("actualizado", SITIO["actualizado"])}</p>')

    # imagen principal del articulo
    img = resolver_imagen(a)
    if img:
        alt = a.get("imagen_alt") or f"{a['titulo']}: gráfico con datos verificados"
        partes.append(
            f'<figure class="figura">'
            f'<img src="img/{escape(img)}" alt="{escape(alt)}" '
            f'width="1200" height="675" loading="eager" decoding="async">'
            f'</figure>')

    partes.append(anuncios.insertar_en_cuerpo(cuerpo_html))

    # bloque de cierre: el lector termino el articulo, maxima atencion
    fin = anuncios.bloque_final()
    if fin:
        partes.append(fin)

    if rel:
        partes.append('<hr><h2>Sigue leyendo</h2><div class="grid">')
        for r in rel:
            partes.append(f"""<a class="card" href="{r['slug']}.html">
<h3>{escape(r['titulo'])}</h3>
<p>{escape(r['descripcion'][:95])}</p></a>""")
        partes.append("</div>")

    partes.append("""<div class="destacado">
<h3>Cómo usamos estos datos</h3>
<p>Las cifras de esta guía provienen de fuentes públicas oficiales y tarifarios de concesionarios
publicados. Los valores son referenciales: tasas municipales, promociones y precios de repuestos
varían. Verifica siempre en la entidad o concesionario antes de decidir.</p></div>""")

    img_art = resolver_imagen(a)
    og = f"https://cuantocuesta.xyz/img/{img_art}" if img_art else ""
    # <title> SEO: usa seo_titulo (max 60 chars) si está definido,
    # dejando el titulo largo solo como H1 visible en la pagina
    seo_t = a.get("seo_titulo") or a["titulo"]
    return pagina(seo_t, a["descripcion"], "\n".join(partes),
                  og_imagen=og, schema=schema_articulo(a, img_art))


def construir_indice(categoria, articulos, nombre, desc, intro=""):
    cat = [a for a in articulos if a["categoria"] == categoria]
    partes = [f'<a class="volver" href="index.html">← Inicio</a>',
              f'<h1>{escape(nombre)}</h1>', f'<p class="lead">{escape(desc)}</p>']
    if intro:
        partes.append(f'<div class="intro-seccion">{intro}</div>')
    if not cat:
        partes.append("<p>Todavía no hay guías publicadas en esta sección.</p>")
    else:
        partes.append('<div class="grid">')
        for a in sorted(cat, key=lambda x: x["titulo"]):
            partes.append(f"""<a class="card" href="{a['slug']}.html">
<h3>{escape(a['titulo'])}</h3>
<p>{escape(a['descripcion'][:110])}</p></a>""")
        partes.append("</div>")
    return pagina(nombre, desc, "\n".join(partes),
                  schema=schema_coleccion(nombre, desc, categoria))


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # copiar imagenes (viven en assets/ para que el build no las borre)
    origen_img = ASSETS / "img"
    if origen_img.exists():
        destino_img = DIST / "img"
        shutil.copytree(origen_img, destino_img)
        print(f"imágenes copiadas: {len(list(destino_img.glob('*.png')))}")

    # AdSense: generar ads.txt ANTES de copiar los estaticos al sitio
    if anuncios.generar_ads_txt():
        print("  ✓ ads.txt generado (vendedor autorizado)")

    # copiar archivos estaticos (verificacion de Google, ads.txt, etc.)
    origen_static = ASSETS / "static"
    if origen_static.exists():
        for f in origen_static.iterdir():
            if f.is_file():
                shutil.copy2(f, DIST / f.name)
        print(f"archivos estáticos copiados: {len(list(origen_static.iterdir()))}")

    articulos = cargar_contenido()
    print(f"artículos encontrados: {len(articulos)}")

    (DIST / "index.html").write_text(construir_home(articulos), encoding="utf-8")

    for a in articulos:
        (DIST / f"{a['slug']}.html").write_text(construir_articulo(a, articulos), encoding="utf-8")
        print(f"  ✓ {a['slug']}.html")

    # páginas índice de todas las categorías
    INDICES = {
        "costos": (
            "Cuánto cuesta mantener cada auto",
            "Desglose real de matrícula, seguro, combustible y mantenimiento por modelo.",
            """<p>Mantener un auto en Ecuador cuesta entre <strong>$73 y $360 al mes</strong> según el
modelo y los kilómetros que hagas. La diferencia no está en el precio de compra: está en el
cilindraje, el rendimiento y el tipo de combustible.</p>
<p>Los rubros que casi nadie suma antes de firmar son cuatro: <strong>matrícula</strong> (rubros del
SRI y la ANT según cilindraje), <strong>seguro</strong> (SPPAT obligatorio, más todo riesgo si lo
contratas), <strong>combustible</strong> y <strong>mantenimiento preventivo</strong>. Este último se
acumula por kilómetro recorrido, no por mes, así que se siente poco a poco y sorprende al final.</p>
<p>Con los precios vigentes (Extra y Ecopaís a <strong>$3,212</strong> el galón, Súper a
<strong>$4,89</strong> y Diésel Premium a <strong>$3,151</strong>) la decisión que más mueve el
resultado es el octanaje: si tu versión admite Extra, usarla en lugar de Súper ahorra más de $500
al año en un SUV mediano.</p>
<p>Usa la <a href="calculadora.html">calculadora de costo mensual</a> para ver tu caso exacto, o
empieza por el desglose de cada modelo abajo.</p>

<h2>Los cuatro rubros, uno por uno</h2>
<p><strong>Matrícula.</strong> Se paga una vez al año y se calcula sobre el avalúo del vehículo, no
sobre lo que pagaste. Incluye rubros del SRI (impuesto a la propiedad, IVA según el segmento) y de
la ANT (tasa de matriculación, placas, calcomanía). El avalúo del SRI se deprecia 20% cada año con
un piso del 10% del precio original, así que un auto de cinco años paga bastante menos que uno nuevo.
Los vehículos híbridos y eléctricos tienen exenciones parciales o totales según el segmento.</p>
<p><strong>Seguro.</strong> El SPPAT (seguro obligatorio de accidentes de tránsito) es mínimo y de
cobertura limitada. El todo riesgo es el rubro donde más varía el precio: entre aseguradoras la
diferencia llega al 40% para el mismo vehículo, y depende de la edad del conductor, el uso declarado,
la deducible elegido y la zona de circulación.</p>
<p><strong>Combustible.</strong> Es el rubro que más se siente mes a mes porque se paga en cada
tanqueada. El gasto no depende solo del rendimiento del motor: depende del octanaje que admite tu
versión. Si el manual permite Extra y estás poniendo Súper, la diferencia supera los $500 al año en
un SUV mediano. Revisa el manual antes de asumir que necesitas la gasolina cara.</p>
<p><strong>Mantenimiento.</strong> Se acumula por kilómetro recorrido, no por mes, y por eso
sorprende. Los servicios de 10.000, 20.000 y 40.000 km tienen costos muy distintos: el de 40.000
suele incluir cambio de bujías, filtros y revisión de frenos, y puede costar varias veces lo que el
servicio básico. El rubro más caro de todos es el cambio de correa de distribución, que en algunos
modelos solo existe cada 100.000 km pero cuesta como un año de mantenimiento junto.</p>

<h2>Los tres errores de cálculo más comunes</h2>
<p><strong>Uno: comparar por rendimiento y no por costo por kilómetro.</strong> Un auto con mejor
rendimiento pero servicio cada 5.000 km puede costar más que otro que rinde menos y se mantiene cada
10.000. Lo que importa es el costo total por kilómetro, no la cifra suelta.</p>
<p><strong>Dos: olvidar la depreciación.</strong> Un auto nuevo pierde entre 15% y 20% de su valor el
primer año. Eso no sale de tu bolsillo como una factura, pero es el costo más grande de tener un
auto, y solo se materializa el día que lo vendes.</p>
<p><strong>Tres: no presupuestar el imprevisto.</strong> Un juego de llantas, un alternador o un
choque sin seguro cubren varios meses del presupuesto mensual. Conviene reservar un fondo aparte en
vez de confiar en que el mes saldrá como el promedio.</p>"""),
        "tramites": (
            "Trámites vehiculares",
            "Matrícula, traspaso de dominio, revisión técnica y certificados: pasos y costos.",
            """<p>Los trámites vehiculares en Ecuador son la parte donde más dinero se pierde por
desinformación: nadie publica los costos completos ni los pasos en orden, y los gestores cobran
por hacer trámites que puedes hacer tú.</p>
<p>Los tres más frecuentes tienen un patrón común: <strong>primero se paga, después se valida el
vehículo</strong>. La matriculación depende del último dígito de la placa, el traspaso de dominio
exige notaría y el 1% del valor del vehículo, y la revisión técnica tiene precio distinto en cada
cantón. Bloqueadores habituales: multas de tránsito sin pagar y gravámenes activos.</p>
<p>Cada guía de esta sección lista el costo de cada rubro, los documentos que debes llevar y los
errores concretos que hacen que el trámite se caiga y tengas que volver.</p>

<h2>Los tres trámites que más se repiten</h2>
<p><strong>Matriculación.</strong> Se hace una vez al año y el calendario depende del <em>último
dígito de la placa</em>: cada dígito tiene su mes asignado. Si llegas tarde pagas recargo e interés,
y si acumulas dos años sin matricular el vehículo puede ser retenido. Antes de ir, verifica que no
tengas multas pendientes: sin eso pagado el sistema rechaza el trámite.</p>
<p><strong>Traspaso de dominio.</strong> Es el más caro y el que más se complica. Requiere
<em>notaría</em> (se reconoce la firma del vendedor), el pago del <strong>1% del valor del
vehículo</strong>, y que el vehículo no tenga gravámenes activos. Si el vendedor no lo quiere hacer,
no aceptes un "traspaso por dentro": la unidad sigue a nombre de él, y cualquier multa o infracción
posterior llega a su nombre; lo que en la práctica te bloquea para vender después.</p>
<p><strong>Revisión técnica vehicular.</strong> Es anual y el <em>precio cambia según el cantón</em>,
porque es una tasa municipal. Revisa frenos, luces, emisiones, suspensión y llantas; si algo falla te
dan un plazo corto para corregir y volver, con costo de reinspección.</p>

<h2>Por qué se caen los trámites</h2>
<p>Casi siempre es por una de estas cuatro razones, y todas se verifican antes de hacer fila:</p>
<ul class="legal">
<li><strong>Multas de tránsito sin pagar.</strong> El sistema bloquea cualquier trámite pendiente.</li>
<li><strong>Gravámenes activos.</strong> Si el auto tiene una prenda o deuda, no se puede transferir
hasta que se levante.</li>
<li><strong>Documentos incompletos.</strong> Falta la matrícula del año anterior, la cédula del
vendedor o el contrato notariado.</li>
<li><strong>Plazos vencidos.</strong> Cada trámite tiene su ventana; pasado el plazo cambia el valor
y a veces el procedimiento.</li>
</ul>

<h2>Hacerlo tú o contratar un gestor</h2>
<p>Los tres trámites se pueden hacer por cuenta propia, y el costo de hacerlo es tiempo en fila más el
valor de las tasas. Un gestor cobra por ese tiempo y por conocer el procedimiento. Si tu caso es un
traspaso con gravamen o una matriculación atrasada, el gestor ahorra más de lo que cobra. Si es una
matriculación al día sin novedades, hacerla tú es perfectamente viable.</p>
<p>Lo que no conviene en ningún caso es firmar un traspaso sin notaría confiando en que "después lo
arreglamos".</p>"""),
        "comparativas": (
            "Comparativas entre modelos",
            "Los autos más vendidos de Ecuador comparados con datos: precio, consumo, seguridad y costos.",
            """<p>Elegir entre dos modelos que cuestan parecido es más fácil con números que con
folletos. El mercado ecuatoriano creció un <strong>41,4% en el primer semestre de 2026</strong>
(récord histórico con <strong>78.185 unidades</strong>) y eso abarató y amplió la oferta: hoy hay
más opciones en cada rango de precio que hace tres años.</p>
<p>Estas comparativas enfrentan modelo contra modelo con los mismos criterios: precio real de
lista, consumo declarado, costo mensual calculado con las tarifas vigentes, seguridad de serie y
valor de reventa. Cuando un dato no está publicado por el fabricante, lo decimos en lugar de
rellenarlo con una estimación disfrazada de certeza.</p>
<p>Ecuador vende el combustible por galón (3,785 litros), así que también comparamos el rendimiento
en las dos unidades para que puedas contrastarlo con la ficha de tu versión.</p>
<p>Si prefieres verlo tú mismo en vez de leer tabla por tabla, el
<strong><a href="comparador.html">comparador interactivo</a></strong> enfrenta dos modelos cualquiera
lado a lado y marca en verde cuál gana en cada campo. Son 18 campos agrupados en precio, motor,
consumo, dimensiones, seguridad y mercado. Cuando un dato no está publicado en la ficha oficial,
la fila dice "No publicado" en vez de estimarlo, y la comparación de ese campo se omite: preferimos
una tabla con huecos visibles a una tabla completa con números inventados.</p>
<p>Tres advertencias antes de decidir con estas tablas. Primero, el precio de lista no es el precio
de calle: los concesionarios publican un precio base y luego suman versiones, accesorios y el
porcentaje de IVA según el segmento. Segundo, el consumo declarado es de laboratorio y en la sierra
rinde distinto que en la costa. Tercero, dos versiones del mismo modelo pueden diferir en seguridad
de serie, así que verifica que estás comparando el mismo nivel de equipamiento.</p>

<h2>Qué comparamos y qué no</h2>
<p><strong>Lo que sí entra en la comparación:</strong> precio de lista por versión, motor y
transmisión, consumo declarado, dimensiones exteriores e interiores, capacidad de maletero,
equipamiento de seguridad de serie, garantía de fábrica y volumen de ventas del modelo en Ecuador
(dato de AEADE).</p>
<p><strong>Lo que no:</strong> sensaciones de manejo, calidad percibida de materiales y confort de
suspensión. Son criterios legítimos para decidir, pero no se pueden comparar con una tabla sin
mentir: depende del uso, de las vías y de cada conductor. Para eso hay que manejar los dos autos.</p>

<h2>Cómo leer estas comparativas</h2>
<p>Empieza por el precio, porque define si los dos modelos compiten de verdad: comparar un auto de
$18.000 con uno de $32.000 no es una comparación, es una descripción. Luego mira el costo mensual
calculado, que incorpora combustible, seguro y mantenimiento con las tarifas vigentes, es el número
que más se parece a tu realidad.</p>
<p>Después vienen los campos donde un modelo suele ganar claramente: consumo (donde un motor más
chico casi siempre gana), espacio interior (donde el más largo gana) y equipamiento de seguridad de
serie (donde la versión importada completa suele ganar).</p>
<p>Por último, el mercado: un modelo con 12.000 unidades vendidas al semestre tiene repuestos en
cualquier ciudad y muchos mecánicos que lo conocen. Uno con 800 unidades no. Ese dato no aparece en
ninguna ficha técnica y decide cuánto vas a sufrir una reparación.</p>

<h2>Tres cosas que cambian el resultado</h2>
<p><strong>La versión.</strong> Dos autos del mismo modelo pueden diferir en bolsas de aire, control
de estabilidad y frenos ABS según el nivel de equipamiento. Compara la versión específica que vas a
comprar, no el modelo en general.</p>
<p><strong>La ciudad.</strong> El rendimiento declarado es de laboratorio. En la sierra, entre
altitud y pendiente, el consumo sube; en la costa y en terreno plano se acerca más al dato de ficha.</p>
<p><strong>El año-modelo.</strong> Un cambio de generación deja las fichas viejas obsoletas. Verifica
que las dos fichas que comparas sean del mismo año-modelo, o el resultado no significa nada.</p>"""),
        "vendidos": (
            "Los más vendidos, analizados uno por uno",
            "Análisis individual de los modelos que dominan el mercado ecuatoriano: precio, consumo, costos y veredicto.",
            """<p>Las cinco marcas que dominaron el mercado ecuatoriano en el primer semestre de 2026
fueron <strong>Kia (12.512 unidades), Chevrolet (9.341), GWM (4.329), Hyundai (4.232) y Toyota
(3.808)</strong>. No es casualidad: son las que tienen la red de concesionarios y repuestos más
densa del país, y eso pesa más de lo que parece cuando necesitas un repuesto en Cuenca o en
Loja.</p>
<p>Cada análisis sigue la misma estructura: ficha técnica, precio por versión, cuánto cuesta
mantenerlo mes a mes, qué tan cómodo es para uso familiar o de trabajo, cómo se comporta en la
sierra y en la costa, y un veredicto claro con el perfil de comprador al que le sirve y al que no.</p>
<p>Comprar lo más vendido tiene una ventaja concreta y medible: repuestos disponibles, mecánicos que
lo conocen y un mercado de usados líquido cuando quieras venderlo. Estas guías te dicen si esa
ventaja compensa el sobreprecio frente a alternativas menos conocidas.</p>

<h2>Por qué conviene saber qué se vende más</h2>
<p>El volumen de ventas no dice si un auto es mejor. Dice algo más práctico: <strong>cuánta red de
soporte tiene</strong>. Un modelo con miles de unidades al año tiene repuestos en stock en las
principales ciudades, mecánicos que ya lo conocen y un mercado de usados líquido.</p>
<p>La diferencia se nota en un caso concreto: cuando un repuesto tarda tres semanas en llegar en vez
de estar en perchas, el auto se queda parado y el costo real de tenerlo sube. Con los modelos
menos vendidos eso pasa con más frecuencia de lo que la ficha técnica sugiere.</p>

<h2>Cómo leer cada análisis</h2>
<p>Cada guía sigue la misma estructura, para que puedas comparar entre modelos sin cambiar de
criterio:</p>
<ul class="legal">
<li><strong>Ficha y versiones:</strong> qué motor, qué transmisión y qué equipamiento trae cada
versión disponible en Ecuador.</li>
<li><strong>Precio por versión:</strong> el precio de lista de cada nivel, para que sepas cuánto
cuesta la versión que realmente quieres y no la de entrada.</li>
<li><strong>Costo mensual:</strong> combustible, seguro y mantenimiento con las tarifas vigentes, al
uso promedio.</li>
<li><strong>Uso real:</strong> cómo se comporta cargado, en ciudad, en carretera y con cinco
ocupantes.</li>
<li><strong>Veredicto:</strong> a qué tipo de comprador le sirve y a cuál no. Un mismo auto puede ser
una buena decisión para una familia y una mala para alguien que viaja solo 40 km al día.</li>
</ul>

<h2>El dato que casi nunca se mira: el valor de reventa</h2>
<p>Los modelos más vendidos mantienen mejor el valor porque hay demanda constante de usados. Un auto
que se vende mucho pierde menos valor que uno con ventas marginales, aunque su precio de lista sea
igual. Si piensas cambiar de auto en cinco años, ese diferencial suele pesar más que la diferencia de
consumo entre dos modelos parecidos.</p>
<p>Considérelo junto con el precio: un modelo $1.500 más caro que aguanta mejor su valor puede
costarte menos al final del ciclo que el más barato de los dos.</p>"""),
        "compra": (
            "Comprar un auto usado",
            "Qué revisar, cómo verificar gravámenes, cómo calcular el precio justo y cómo detectar un choque.",
            """<p>El mercado de usados en Ecuador es donde está el riesgo real: un carro chocado o
inundado puede verse impecable y fallar meses después. La buena noticia es que <strong>casi todo
es verificable antes de pagar</strong>.</p>
<p>Tres verificaciones que cuestan poco y evitan pérdidas grandes: consultar <strong>gravámenes y
multas</strong> en el sistema de la ANT, revisar el <strong>CUV</strong> para ver el historial de
transferencias, y calcular el <strong>precio justo</strong> con el avalúo del SRI (que se deprecia
20% cada año con un piso del 10% del precio original) antes de sentarte a negociar.</p>
<p>También conviene saber qué no te dice nadie: la transferencia de dominio requiere notaría y el
1% del valor, y si el vendedor desaparece después de cobrar, el trámite se complica mucho más de
lo que la gente anticipa.</p>
<p>Un usado no se inspecciona con la vista. Dos cosas que se hacen antes de pagar y que la mayoría
omite: pedir el historial de mantenimiento (facturas de taller con kilometraje, no el cuaderno de
mantenimiento lleno a mano) y llevar la unidad a un mecánico independiente, no al taller que el
vendedor recomienda. Una revisión en elevador cuesta poco y muestra lo que el vistazo en la vereda
no ve: fugas, óxido estructural, soldaduras en el larguero y desgaste irregular de llantas, que
delata un choque mal reparado.</p>
<p>El kilometraje del tablero no es confiable por sí solo. Contrástalo con el desgaste real: los
pedales, el volante, la palanca y los asientos cuentan una historia distinta si el auto declara
40.000 km y tiene 120.000. Y si el auto tiene gravamen activo, no lo compres así haya acuerdo de
palabras: la prenda sigue a la unidad, no al dueño anterior, y la puedes terminar pagando tú.</p>

<h2>El orden correcto de la verificación</h2>
<p>Comprar un usado tiene una secuencia que conviene no invertir. Primero se <strong>verifica el
papel</strong>, después se <strong>inspecciona el auto</strong>, y solo entonces se <strong>negocia el
precio</strong>. Hacerlo al revés es lo que produce los arrepentimientos: cuando ya te enamoraste del
auto, es mucho más difícil caminar si aparece un gravamen.</p>
<ul class="legal">
<li><strong>1. Papel:</strong> consulta de gravámenes y multas, y el historial de transferencias del
CUV. Es gratis o casi gratis y descarta autos antes de moverte.</li>
<li><strong>2. Precio:</strong> calcula el rango justo con el avalúo del SRI antes de escuchar la
cifra del vendedor, para llegar con un número propio.</li>
<li><strong>3. Auto:</strong> revisión en elevador con un mecánico independiente. No el taller que el
vendedor recomienda.</li>
<li><strong>4. Cierre:</strong> traspaso en notaría con el 1% pagado. Nunca "por dentro".</li>
</ul>

<h2>Señales de un auto chocado o inundado</h2>
<p>Un carro reparado puede verse impecable. Lo que delata el trabajo son las inconsistencias:</p>
<ul class="legal">
<li><strong>Pintura distinta entre paneles</strong> bajo luz natural, o bordes con exceso de
sellador.</li>
<li><strong>Tornillos de carrocería con marcas de llave</strong>: señal de que el panel se desmontó.</li>
<li><strong>Desgaste irregular de llantas</strong>, sobre todo en una sola rueda: el eje puede estar
desalineado por un golpe.</li>
<li><strong>Óxido o humedad bajo las alfombras y en los raíles del asiento</strong>: rastro de
inundación.</li>
<li><strong>Olor a humedad persistente</strong> que no se va con ventilación.</li>
<li><strong>Vidrios con fecha distinta al año del auto</strong>: señal de reemplazo por siniestro.</li>
</ul>

<h2>El kilometraje y el precio</h2>
<p>El kilometraje del tablero no es prueba de nada por sí solo: se puede modificar. Se contrasta con
el desgaste real de pedales, volante, palanca y asientos. Un auto que declara 40.000 km y muestra
pedales gastados tiene otra historia.</p>
<p>Para el precio, el avalúo del SRI es el punto de partida: se deprecia <strong>20% cada año</strong>
con un piso del 10% del precio original. El valor de mercado real puede estar por encima o por debajo
del avalúo según el modelo y su demanda, pero el avalúo te da el número con el que el sistema calcula
los impuestos; y con el que puedes discutir el precio del vendedor sin quedar en desventaja.</p>"""),
        "electricos": (
            "Eléctricos e híbridos",
            "Catálogo, costos reales de carga, incentivos tributarios y red de electrolineras en Ecuador.",
            """<p>Los vehículos electrificados ya representan alrededor del <strong>18% de las ventas
nuevas</strong> en Ecuador, y el ritmo sigue subiendo. Pero la información práctica (cuánto cuesta
cargar de verdad, cuánto se ahorra frente a gasolina, qué incentivos existen) está dispersa o
directamente no existe.</p>
<p>Los números, para que los tengas claros: cargar un eléctrico cuesta entre <strong>$8 y $10</strong>
por carga completa en tarifa residencial, contra los <strong>$43,97</strong> que cuesta el
combustible de un sedán a gasolina en 1.000 km. En costo mensual, un eléctrico compacto ronda los
<strong>$37,50</strong> frente a los <strong>$75,97</strong> de su equivalente a gasolina.</p>
<p>Las barreras reales no son el costo por kilómetro: son la red de carga pública, el tiempo de
recarga y la disponibilidad de talleres especializados fuera de Quito y Guayaquil. Estas guías
cubren las tres con datos del catálogo ecuatoriano.</p>
<p>Antes de firmar, conviene entender qué se está comprando con un eléctrico en Ecuador. Los
incentivos tributarios existen (arancel cero para el segmento y exención del ICE en varios casos),
pero se aplican sobre un precio de lista que ya viene alto porque casi todas las unidades llegan
importadas de China. El ahorro real aparece en la operación, no en la compra: quien carga en casa
en tarifa residencial nocturna gasta una fracción de lo que cuesta el combustible equivalente, y
quien depende de cargadores públicos rápidos gasta bastante más.</p>
<p>La garantía de la batería es el dato que casi nadie revisa y el que más pesa a cinco años.
Pregunta por la cobertura específica sobre la batería de tracción (años y kilómetros, que suelen
ser dos cifras distintas), qué porcentaje de degradación cubre el reemplazo y qué taller de la red
ecuatoriana atiende ese trabajo. Un vehículo con buena autonomía y sin taller a menos de 400 km
obliga a mover la unidad para cualquier reparación mayor.</p>

<h2>Qué revisar antes de comprar un eléctrico en Ecuador</h2>
<ul class="legal">
<li><strong>Autonomía real, no la homologada.</strong> El ciclo de homologación es optimista. En la
sierra, con frío y pendiente, la autonomía baja de forma notable; pide el dato de uso real, no el de
la ficha.</li>
<li><strong>Garantía de la batería de tracción.</strong> Años y kilómetros son dos cifras distintas,
y el menor de los dos manda. Pregunta qué porcentaje de degradación cubre el reemplazo.</li>
<li><strong>Taller de la red en tu ciudad.</strong> Un vehículo con buena autonomía pero sin taller
cerca obliga a moverlo para cualquier reparación mayor.</li>
<li><strong>Tipo de cargador a bordo.</strong> Determina cuánto tardas realmente en cargar. La
velocidad máxima de carga suele estar limitada por el cargador del auto, no por la electrolinera.</li>
<li><strong>Peso y costo de llantas.</strong> Los eléctricos pesan más por la batería y gastan llantas
más rápido y más caras. Es un rubro de mantenimiento que casi nunca se suma.</li>
</ul>

<h2>Eléctrico puro o híbrido: la decisión práctica</h2>
<p>Un <strong>híbrido convencional</strong> no se enchufa y no depende de la red de carga: consume
menos que un gasolina en ciudad y no cambia tu rutina. Un <strong>eléctrico puro</strong> cuesta mucho
menos por kilómetro, pero depende de dónde cargas.</p>
<p>La regla práctica: si puedes cargar en casa todas las noches y tu recorrido diario entra en el
rango de autonomía con margen, el eléctrico puro gana en costo de operación de forma clara. Si
dependes de cargadores públicos rápidos o haces viajes largos frecuentes, el ahorro se reduce y la
logística se complica. Ahí el híbrido suele ser la decisión correcta.</p>

<h2>Los incentivos y sus límites</h2>
<p>Los incentivos tributarios existen (arancel reducido o cero para el segmento, exención del ICE en
varios casos), pero se aplican sobre un precio de lista que ya viene alto porque buena parte de las
unidades llegan importadas. El efecto real está en la operación: quien carga en casa en tarifa
residencial gasta una fracción del equivalente en combustible; quien depende de carga pública rápida
gasta bastante más.</p>
<p>Antes de firmar, confirma qué incentivo aplica a la versión específica que estás comprando. No
todas las versiones del mismo modelo califican igual.</p>"""),
    }
    for cat, (nombre, desc, intro) in INDICES.items():
        (DIST / f"{cat}.html").write_text(
            construir_indice(cat, articulos, nombre, desc, intro), encoding="utf-8")

    # páginas legales (obligatorias para AdSense)
    (DIST / "privacidad.html").write_text(pagina(
        "Política de privacidad | Autos Ecuador",
        "Cómo Autos Ecuador trata los datos de sus visitantes, uso de cookies y publicidad.",
        """<a class="volver" href="index.html">← Inicio</a>
<h1>Política de privacidad</h1>
<p class="meta">Última actualización: """ + SITIO["actualizado"] + """</p>

<h2>Qué datos recopilamos</h2>
<p>Autos Ecuador es un sitio de contenido informativo. No solicitamos registro, no pedimos datos
personales y no vendemos información a terceros.</p>
<ul class="legal">
<li><strong>Datos de navegación anónimos:</strong> páginas visitadas, tiempo de permanencia, tipo de
dispositivo y navegador, y región aproximada. Se usan para entender qué contenido resulta útil.</li>
<li><strong>Datos que tú envías voluntariamente:</strong> si nos escribes por correo, conservamos tu
mensaje para responderte.</li>
</ul>

<h2>Cookies</h2>
<p>Este sitio usa cookies para recordar preferencias y para medir audiencia de forma agregada.
Puedes bloquear o eliminar cookies desde la configuración de tu navegador; el sitio seguirá funcionando.
El detalle completo está en la <a href="cookies.html">política de cookies</a>.</p>

<h2>Publicidad y terceros</h2>
<p>Este sitio muestra anuncios servidos por <strong>Google AdSense</strong> y puede usar otras redes
publicitarias. Como consecuencia de esa publicidad, <strong>terceros distintos de nosotros pueden
colocar y leer cookies en tu navegador</strong>, así como usar identificadores como direcciones IP o
web beacons para recopilar información.</p>
<ul class="legal">
<li>Google, como proveedor externo, usa cookies para publicar anuncios en este sitio.</li>
<li>La cookie de <strong>DoubleClick DART</strong> permite a Google y sus socios mostrar anuncios
basados en tus visitas a este y a otros sitios de internet.</li>
<li>Puedes inhabilitar la publicidad personalizada de Google en
<a href="https://www.google.com/settings/ads" rel="nofollow noopener" target="_blank">Configuración de anuncios de Google</a>.</li>
<li>También puedes inhabilitar el uso de cookies de terceros en
<a href="https://www.aboutads.info/choices/" rel="nofollow noopener" target="_blank">aboutads.info</a>.</li>
</ul>
<p>Más información sobre cómo Google trata los datos de los sitios de sus socios:
<a href="https://policies.google.com/technologies/partner-sites" rel="nofollow noopener" target="_blank">Cómo usa Google los datos</a>.</p>
<p class="meta">En el Espacio Económico Europeo, Reino Unido y Suiza se muestra un aviso de
consentimiento que permite aceptar, gestionar o rechazar el uso de cookies publicitarias.</p>

<h2>Enlaces a terceros</h2>
<p>Algunos artículos enlazan a sitios oficiales (SRI, ANT, municipios) o a páginas de concesionarios y
aseguradoras. No controlamos esos sitios ni sus políticas de privacidad.</p>

<h2>Menores de edad</h2>
<p>El contenido de este sitio es de carácter informativo general y no está dirigido a menores de 18 años.</p>

<h2>Cambios en esta política</h2>
<p>Si esta política cambia, la fecha de actualización al inicio de la página se modificará. El uso
continuado del sitio implica la aceptación de la versión vigente.</p>

<h2>Contacto</h2>
<p>Para consultas sobre esta política, escríbenos desde la página de <a href="contacto.html">contacto</a>.</p>"""), encoding="utf-8")

    # política de cookies (requisito explícito de Google Publisher Policies)
    (DIST / "cookies.html").write_text(pagina(
        "Política de cookies | Autos Ecuador",
        "Qué cookies usa este sitio, para qué sirven y cómo puedes controlarlas.",
        """<a class="volver" href="index.html">← Inicio</a>
<h1>Política de cookies</h1>
<p class="meta">Última actualización: """ + SITIO["actualizado"] + """</p>

<h2>Qué es una cookie</h2>
<p>Es un archivo pequeño que un sitio guarda en tu navegador. Sirve para recordar preferencias y para
medir cómo se usa el sitio. No ejecuta programas ni accede a tus archivos.</p>

<h2>Qué usamos</h2>
<ul class="legal">
<li><strong>Funcionales:</strong> recuerdan tus preferencias de lectura. Sin ellas el sitio funciona,
pero pierdes esas comodidades. No se comparten con terceros.</li>
<li><strong>De medición:</strong> registran páginas visitadas, tiempo de permanencia y tipo de
dispositivo, de forma agregada. Nos dicen qué contenido resulta útil y cuál hay que mejorar.</li>
<li><strong>Publicitarias:</strong> las colocan Google AdSense y otras redes para mostrar anuncios.
Son las únicas que pueden identificar tu navegador en otros sitios.</li>
</ul>

<h2>Cookies de terceros</h2>
<p>Al mostrarse publicidad, <strong>Google y sus socios pueden colocar y leer cookies en tu
navegador</strong> y usar identificadores como direcciones IP o web beacons. La cookie
<strong>DoubleClick DART</strong> permite mostrar anuncios basados en tus visitas a este y a otros
sitios. No controlamos esas cookies: las rige la política de privacidad de cada proveedor.</p>
<p>Más información: <a href="https://policies.google.com/technologies/partner-sites" rel="nofollow noopener" target="_blank">Cómo usa Google los datos de los sitios de sus socios</a>.</p>

<h2>Cómo controlarlas</h2>
<ul class="legal">
<li><strong>Anuncios personalizados de Google:</strong> desactívalos en
<a href="https://www.google.com/settings/ads" rel="nofollow noopener" target="_blank">Configuración de anuncios</a>.</li>
<li><strong>Cookies de terceros en general:</strong> gestiónalas en
<a href="https://www.aboutads.info/choices/" rel="nofollow noopener" target="_blank">aboutads.info</a>.</li>
<li><strong>Desde tu navegador:</strong> todos los navegadores permiten ver, bloquear y borrar
cookies desde su configuración de privacidad. Bloquearlas no impide leer el sitio.</li>
<li><strong>Modo privado:</strong> al cerrar la ventana se descartan las cookies de la sesión.</li>
</ul>

<h2>Consentimiento</h2>
<p>En el Espacio Económico Europeo, Reino Unido y Suiza se muestra un aviso que permite aceptar,
gestionar o rechazar las cookies publicitarias antes de que se activen. Fuera de esas regiones, el uso
continuado del sitio se entiende como aceptación de esta política.</p>

<h2>Cambios</h2>
<p>Si cambiamos las cookies que usamos, actualizamos la fecha al inicio de esta página.</p>

<h2>Contacto</h2>
<p>Dudas sobre esta política: escríbenos desde la página de <a href="contacto.html">contacto</a>.</p>"""),
        encoding="utf-8")

    (DIST / "acerca.html").write_text(pagina(
        "Acerca de | Autos Ecuador",
        "Quiénes somos y cómo verificamos los datos de costos, trámites y comparativas de autos en Ecuador.",
        """<a class="volver" href="index.html">← Inicio</a>
<h1>Acerca de Autos Ecuador</h1>

<p class="lead">Información verificable para decidir con números, no con intuición.</p>

<h2>Por qué existe este sitio</h2>
<p>Comprar y mantener un auto en Ecuador está lleno de cifras dispersas: la matrícula tiene cinco
rubros distintos, el seguro varía hasta 40% entre aseguradoras, y nadie publica cuánto cuesta el
servicio de los 60.000 km antes de que firmes.</p>
<p>Cuando buscamos esa información para una decisión propia, encontramos lo mismo en todas partes:
blogs con cifras sin fuente, foros con respuestas de hace seis años y publicaciones que mezclan
precios de otros países. Los datos existían, pero estaban repartidos entre el SRI, la ANT, los
tarifarios municipales, las fichas de fabricante y los reportes sectoriales.</p>
<p>Este sitio reúne esos datos en un solo lugar, con la fuente de cada cifra.</p>

<h2>Qué vas a encontrar aquí</h2>
<p>El contenido está organizado en cuatro áreas que cubren el ciclo completo de tener un auto en
Ecuador: <a href="costos.html">costos de mantenimiento</a> por modelo, <a href="tramites.html">trámites
vehiculares</a> con pasos y valores, <a href="comparativas.html">comparativas</a> entre modelos que
compiten en el mismo rango de precio, y <a href="compra.html">guías para comprar un usado</a> sin
llevarte una sorpresa.</p>
<p>Además hay dos herramientas que no son artículos: la <a href="calculadora.html">calculadora de
costo mensual</a>, que estima el gasto real de un modelo con tus kilómetros y el precio del
combustible vigente, y el <a href="comparador.html">comparador interactivo</a>, que enfrenta dos
modelos en 18 campos y marca cuál gana en cada uno.</p>

<h2>Cómo trabajamos</h2>
<ul class="legal">
<li><strong>Fuentes oficiales primero:</strong> SRI, ANT, GAD municipales y el COOTAD para todo lo
relacionado con impuestos, tasas y trámites.</li>
<li><strong>Datos de mercado:</strong> AEADE para volúmenes de venta y comportamiento del sector.</li>
<li><strong>Tarifarios de concesionarios:</strong> costos de mantenimiento publicados por talleres
autorizados, no estimaciones.</li>
<li><strong>Fichas de fabricante:</strong> especificaciones técnicas, consumo declarado y equipamiento
de serie, tomadas de la ficha oficial de cada versión.</li>
<li><strong>Tarifas de servicios:</strong> pliegos tarifarios publicados para electricidad,
combustibles y peajes.</li>
</ul>

<h2>La regla que no rompemos</h2>
<p><strong>Sin cifras inventadas.</strong> Cuando un dato no se puede verificar en una fuente oficial,
lo decimos en lugar de rellenarlo con una estimación que parece un hecho.</p>
<p>Eso significa que vas a ver huecos visibles. En el comparador, un campo sin dato oficial dice
<em>"No publicado"</em> y la comparación de ese campo se omite, en vez de asumir un valor. En las
fichas de modelo, si el fabricante no publica un dato para esa versión, aparece la ausencia en vez
de un promedio de la competencia.</p>
<p>Una tabla con huecos es menos vistosa que una tabla completa. También es la única que te sirve
para decidir.</p>

<h2>Cómo se financia</h2>
<p>El sitio se sostiene con publicidad display. No vendemos autos, no cobramos por reseñar un modelo
y no aceptamos pagos de concesionarios o aseguradoras por aparecer mejor posicionados. Si en algún
momento un contenido pagado existe, estará identificado como tal.</p>

<h2>Nuestro límite</h2>
<p>Los valores que publicamos son <strong>referenciales</strong>. Las tasas municipales cambian de
cantón a cantón, los precios de repuestos varían entre talleres y las promociones de concesionaria
son temporales. Verifica siempre en la entidad o el establecimiento antes de decidir.</p>
<p><strong>No somos asesoría legal, contable ni financiera.</strong> Si tu caso tiene implicaciones
legales o tributarias, consulta con un profesional.</p>

<h2>Errores y correcciones</h2>
<p>Un dato desactualizado es un dato equivocado, y nos interesa saberlo. Si encuentras una cifra que
no cuadra con lo que te cobraron o con lo que dice la entidad, escríbenos desde la página de
<a href="contacto.html">contacto</a> indicando el artículo. Corregimos y anotamos la fuente nueva.</p>

<h2>Cómo se actualiza</h2>
<p>Revisamos las guías cuando cambian las tasas, los tarifarios o el mercado. Los rubros que más se
mueven son los combustibles (precio fijado por el Estado), la matrícula (se recalcula cada año con
el avalúo del vehículo) y los tarifarios de mantenimiento de las marcas. Cada artículo muestra su
fecha de actualización al inicio, para que sepas qué tan reciente es lo que estás leyendo.</p>"""), encoding="utf-8")

    (DIST / "contacto.html").write_text(pagina(
        "Contacto | Autos Ecuador",
        "Escríbenos para corregir un dato, sugerir un tema o consultar por colaboraciones.",
        """<a class="volver" href="index.html">← Inicio</a>
<h1>Contacto</h1>

<h2>Escríbenos</h2>
<p>Si encontraste un dato desactualizado, tienes una duda sobre un trámite o quieres sugerir un tema,
nos interesa saberlo.</p>

<div class="destacado">
<h3>Correo</h3>
<p>Escríbenos indicando el tema en el asunto. Si tu mensaje es sobre un artículo, incluye el enlace
para ubicarlo rápido.</p>
</div>

<h2>Qué respondemos</h2>
<ul class="legal">
<li><strong>Correcciones de datos:</strong> con prioridad. Si una tasa o precio cambió, lo corregimos
y anotamos la fuente.</li>
<li><strong>Sugerencias de temas:</strong> bienvenidas. Si un modelo o trámite no está cubierto, lo
agregamos al plan de contenido.</li>
<li><strong>Colaboraciones y publicidad:</strong> escríbenos con la propuesta.</li>
</ul>

<h2>Cómo enviar una corrección útil</h2>
<p>Para corregir una cifra rápido necesitamos tres cosas: <strong>el artículo</strong> (el enlace),
<strong>el dato que no cuadra</strong> y <strong>de dónde sale el valor correcto</strong> (una factura,
el tarifario del municipio, la página de la entidad). Con eso verificamos y actualizamos en la misma
semana.</p>
<p>Si es un dato de mercado que cambió, menciona la fecha: un precio de concesionaria de hace seis
meses no sirve para contrastar el de hoy.</p>

<h2>Qué no hacemos</h2>
<p>No brindamos asesoría legal, contable ni financiera personalizada. Si tu consulta es sobre una
situación particular con implicaciones legales, acude a un profesional o a la entidad correspondiente.</p>
<p>Tampoco intervenimos en trámites, no representamos a nadie ante el SRI ni la ANT, y no gestionamos
compraventas de vehículos. Este sitio publica información; los trámites los haces tú o un gestor de
tu confianza.</p>

<h2>Antes de escribir, revisa esto</h2>
<p>Buena parte de las consultas que llegan ya están respondidas en el sitio. Vale la pena revisar
primero la <a href="costos.html">sección de costos</a>, la de <a href="tramites.html">trámites</a> o
la <a href="calculadora.html">calculadora de costo mensual</a>: cubren las preguntas más frecuentes
sobre matrícula, seguros, combustible y mantenimiento por modelo.</p>"""), encoding="utf-8")

    # calculadora interactiva (activo de posicionamiento: herramienta real)
    try:
        import calculadora as _calc
        _calc.main()
    except Exception as e:
        print(f"  ⚠ calculadora no generada: {e}")

    # comparador de modelos (interactivo + paginas estaticas por par)
    try:
        import comparador
        n, archivos = comparador.generar_todo(raiz=str(BASE), paginas=pagina)
        print(f"  ✓ comparador: {n} archivos generados")
        pares = [a for a in archivos if a.startswith("comparar/")]
    except Exception as e:
        print(f"  ⚠ comparador no generado: {e}")
        archivos, pares = [], []

    # sitemap
    urls = (["index.html", "costos.html", "tramites.html", "comparativas.html",
             "vendidos.html", "compra.html", "electricos.html",
             "privacidad.html", "cookies.html", "acerca.html", "contacto.html",
             "calculadora.html", "comparador.html"]
            + pares
            + [f"{a['slug']}.html" for a in articulos])
    # sitemap con URLs absolutas (Google las exige)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        loc = f"{SITIO['url']}/" if u == "index.html" else f"{SITIO['url']}/{u}"
        # portada e índices con prioridad alta, legales con prioridad baja
        if u == "index.html":
            pri = "1.0"
        elif u in ("privacidad.html", "acerca.html", "contacto.html"):
            pri = "0.3"
        elif ".html" in u and u.count("-") < 2:
            pri = "0.8"
        else:
            pri = "0.9"
        sm.append(f"<url><loc>{loc}</loc>"
                  f"<lastmod>{SITIO['actualizado']}</lastmod>"
                  f"<priority>{pri}</priority></url>")
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITIO['url']}/sitemap.xml\n",
        encoding="utf-8")

    print(f"\n✓ sitio generado en {DIST}")
    print(f"  {len(list(DIST.glob('*.html')))} páginas HTML")


if __name__ == "__main__":
    main()
