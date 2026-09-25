#!/usr/bin/env python3
"""
Generador de sitio estático — Portal automotriz Ecuador.
Sin dependencias externas. Solo stdlib.

Uso:
    python3 build.py

Salida: dist/
"""
import json
import os
import re
import shutil
import unicodedata
from datetime import date
from html import escape
from pathlib import Path

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
@media(max-width:600px){
 h1{font-size:1.5rem}h2{font-size:1.15rem}
 nav a{margin-left:0;margin-right:14px;display:inline-block}
 table{font-size:.82rem}
}
"""


def pagina(titulo, descripcion, cuerpo, ruta_rel="", canonical="", og_imagen="", schema=""):
    nav = ('<nav><a href="' + ruta_rel + 'index.html">Inicio</a>'
           '<a href="' + ruta_rel + 'costos.html">Costos</a>'
           '<a href="' + ruta_rel + 'tramites.html">Trámites</a>'
           '<a href="' + ruta_rel + 'vendidos.html">Más vendidos</a>'
           '<a href="' + ruta_rel + 'comparativas.html">Comparativas</a>'
           '<a href="' + ruta_rel + 'electricos.html">Eléctricos</a></nav>')
    og = f'<meta property="og:image" content="{escape(og_imagen)}">' if og_imagen else ""
    tw = '<meta name="twitter:card" content="summary_large_image">' if og_imagen else ""
    ld = "\n".join(
        f'<script type="application/ld+json">{s}</script>' for s in schema
    ) if schema else ""
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
<p><strong>Autos Ecuador</strong> — {escape(SITIO['tagline'])}</p>
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
    for c in orden_cats + [k for k in cats if k not in orden_cats]:
        if c not in cats:
            continue
        partes.append(f'<h2 id="{c}">{escape(nombres.get(c, c.title()))}</h2><div class="grid">')
        for a in sorted(cats[c], key=lambda x: x["titulo"]):
            partes.append(f"""<a class="card" href="{a['slug']}.html">
<h3>{escape(a['titulo'])}</h3>
<p>{escape(a['descripcion'][:105])}</p></a>""")
        partes.append("</div>")

    return pagina(
        "Autos Ecuador — Costos, trámites y comparativas de autos",
        SITIO["descripcion"],
        "\n".join(partes),
        canonical=f"{SITIO['url']}/",
        schema=schema_sitio(),
    )


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
        alt = a.get("imagen_alt") or f"{a['titulo']} — gráfico con datos verificados"
        partes.append(
            f'<figure class="figura">'
            f'<img src="img/{escape(img)}" alt="{escape(alt)}" '
            f'width="1200" height="675" loading="eager" decoding="async">'
            f'</figure>'
        )

    partes.append(cuerpo_html)

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


def construir_indice(categoria, articulos, nombre, desc):
    cat = [a for a in articulos if a["categoria"] == categoria]
    partes = [f'<a class="volver" href="index.html">← Inicio</a>',
              f'<h1>{escape(nombre)}</h1>', f'<p class="lead">{escape(desc)}</p>']
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

    # copiar archivos estaticos (verificacion de Google, etc.)
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
        "costos": ("Cuánto cuesta mantener cada auto",
                   "Desglose real de matrícula, seguro, combustible y mantenimiento por modelo."),
        "tramites": ("Trámites vehiculares",
                     "Matrícula, traspaso de dominio, revisión técnica y certificados: pasos y costos."),
        "comparativas": ("Comparativas entre modelos",
                         "Los autos más vendidos de Ecuador comparados con datos: precio, consumo, seguridad y costos."),
        "vendidos": ("Los más vendidos, analizados uno por uno",
                     "Análisis individual de los modelos que dominan el mercado ecuatoriano: precio, consumo, costos y veredicto."),
        "compra": ("Comprar un auto usado",
                   "Qué revisar, cómo verificar gravámenes, cómo calcular el precio justo y cómo detectar un choque."),
        "electricos": ("Eléctricos e híbridos",
                       "Catálogo, costos reales de carga, incentivos tributarios y red de electrolineras en Ecuador."),
    }
    for cat, (nombre, desc) in INDICES.items():
        (DIST / f"{cat}.html").write_text(
            construir_indice(cat, articulos, nombre, desc), encoding="utf-8")

    # páginas legales (obligatorias para AdSense)
    (DIST / "privacidad.html").write_text(pagina(
        "Política de privacidad — Autos Ecuador",
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
        "Política de cookies — Autos Ecuador",
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
        "Acerca de — Autos Ecuador",
        "Quiénes somos y cómo verificamos los datos de costos, trámites y comparativas de autos en Ecuador.",
        """<a class="volver" href="index.html">← Inicio</a>
<h1>Acerca de Autos Ecuador</h1>

<p class="lead">Información verificable para decidir con números, no con intuición.</p>

<h2>Por qué existe este sitio</h2>
<p>Comprar y mantener un auto en Ecuador está lleno de cifras dispersas: la matrícula tiene cinco
rubros distintos, el seguro varía hasta 40% entre aseguradoras, y nadie publica cuánto cuesta el
servicio de los 60.000 km antes de que firmes.</p>
<p>Este sitio reúne esos datos en un solo lugar, con la fuente de cada cifra.</p>

<h2>Cómo trabajamos</h2>
<ul class="legal">
<li><strong>Fuentes oficiales primero:</strong> SRI, ANT, GAD municipales y el COOTAD para todo lo
relacionado con impuestos, tasas y trámites.</li>
<li><strong>Datos de mercado:</strong> AEADE para volúmenes de venta y comportamiento del sector.</li>
<li><strong>Tarifarios de concesionarios:</strong> costos de mantenimiento publicados por talleres
autorizados, no estimaciones.</li>
<li><strong>Sin cifras inventadas.</strong> Cuando un dato no se puede verificar, lo decimos en
lugar de rellenarlo.</li>
</ul>

<h2>Nuestro límite</h2>
<p>Los valores que publicamos son <strong>referenciales</strong>. Las tasas municipales cambian de
cantón a cantón, los precios de repuestos varían entre talleres y las promociones de concesionaria
son temporales. Verifica siempre en la entidad o el establecimiento antes de decidir.</p>
<p><strong>No somos asesoría legal, contable ni financiera.</strong> Si tu caso tiene implicaciones
legales o tributarias, consulta con un profesional.</p>

<h2>Cómo se actualiza</h2>
<p>Revisamos las guías cuando cambian las tasas, los tarifarios o el mercado. Cada artículo muestra su
fecha de actualización al inicio.</p>"""), encoding="utf-8")

    (DIST / "contacto.html").write_text(pagina(
        "Contacto — Autos Ecuador",
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

<h2>Qué no hacemos</h2>
<p>No brindamos asesoría legal, contable ni financiera personalizada. Si tu consulta es sobre una
situación particular con implicaciones legales, acude a un profesional o a la entidad correspondiente.</p>"""), encoding="utf-8")

    # sitemap
    urls = (["index.html", "costos.html", "tramites.html", "comparativas.html",
             "vendidos.html", "compra.html", "electricos.html",
             "privacidad.html", "cookies.html", "acerca.html", "contacto.html"]
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
