"""
Comparador de modelos para Autos Ecuador / cuantocuesta.xyz
============================================================

Genera dos cosas a partir de data/modelos.json:

  1. comparador.html          -> herramienta interactiva (elige dos, compara)
  2. comparar/<a>-vs-<b>.html -> paginas estaticas por par (SEO + AdSense)

Todo es estatico y corre en el navegador: sirve para GitHub Pages.
Las paginas estaticas existen porque el HTML pre-renderizado es lo que
Google indexa; la herramienta interactiva sola no posiciona.

REGLA DE DATOS (no negociable): si un campo falta, se muestra
"No publicado" y la fila NO se compara. Nunca se rellena con estimaciones.
"""

import json
import os
from html import escape

# ---------------------------------------------------------------------------
# Definicion de campos comparables
# ---------------------------------------------------------------------------
# dir: "menor" = el valor mas bajo gana | "mayor" = el mas alto gana
#       None    = dato informativo, no se compara (texto libre)
# fmt: como se muestra el valor
CAMPOS = [
    # clave json        etiqueta                 unidad      dir      grupo
    ("precio_desde",   "Precio desde",           "USD",      "menor", "precio"),
    ("precio_hasta",   "Precio hasta",           "USD",      "menor", "precio"),
    ("cilindrada_cc",  "Cilindrada",             "cc",       None,    "motor"),
    ("potencia_hp",    "Potencia",               "hp",       "mayor", "motor"),
    ("torque_nm",      "Torque",                 "Nm",       "mayor", "motor"),
    ("transmision",    "Transmision",            "",         None,    "motor"),
    ("motor",          "Motor",                  "",         None,    "motor"),
    ("consumo_urbano", "Consumo urbano",         "km/l",     "mayor", "consumo"),
    ("consumo_carretera", "Consumo carretera",   "km/l",     "mayor", "consumo"),
    ("consumo_mixto",  "Consumo mixto",          "km/l",     "mayor", "consumo"),
    ("tanque_l",       "Tanque de combustible",  "L",        "mayor", "consumo"),
    ("maletero_l",     "Maletero",               "L",        "mayor", "cuerpo"),
    ("peso_kg",        "Peso",                   "kg",       "menor", "cuerpo"),
    ("airbags",        "Airbags",                "",         "mayor", "seguridad"),
    ("garantia",       "Garantia",               "",         None,    "seguridad"),
    ("origen",         "Origen",                 "",         None,    "cuerpo"),
    ("unidades_2025",  "Unidades vendidas 2025", "",         "mayor", "mercado"),
    ("segmento",       "Segmento",               "",         None,    "mercado"),
    ("versiones",      "Versiones disponibles",  "",         None,    "mercado"),
]

# Campos que cuentan para decidir si un modelo esta "bien documentado".
# Los de texto libre (garantia, origen, versiones...) no cuentan: casi
# siempre estan vacios y no aportan a la comparacion numerica.
CAMPOS_CLAVE = [
    "precio_desde", "potencia_hp", "torque_nm", "consumo_mixto",
    "tanque_l", "maletero_l", "peso_kg", "airbags",
]

# Minimo de campos clave cargados para que un modelo entre al comparador.
# Un modelo con 2 de 8 produce comparaciones tipo "gana 1 de 2", que es
# contenido vacio y juega en contra del SEO y de AdSense.
MINIMO_DATOS = 5


GRUPOS = {
    "precio":    "Precio",
    "motor":     "Motor y transmision",
    "consumo":   "Consumo y autonomia",
    "cuerpo":    "Dimensiones y peso",
    "seguridad": "Seguridad y garantia",
    "mercado":   "Mercado",
}


def _num(v):
    """Devuelve el valor como numero, o None si no sirve para comparar."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _muestra(v, unidad):
    """Formatea un valor para mostrarlo. Devuelve None si no hay dato."""
    if v is None or v == "" or (isinstance(v, list) and not v):
        return None
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    if unidad == "USD":
        n = _num(v)
        if n is not None:
            return "USD " + format(int(n), ",d").replace(",", ".")
        return None
    if isinstance(v, (int, float)) and float(v).is_integer():
        return f"{int(v)} {unidad}".strip()
    return f"{v} {unidad}".strip()


def cargar_modelos(ruta="data/modelos.json"):
    """Lee models.json y devuelve la lista de modelos."""
    with open(ruta, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("modelos", []), d.get("meta", {})


# ---------------------------------------------------------------------------
# 1. Herramienta interactiva
# ---------------------------------------------------------------------------

def _js_datos(modelos):
    """Los modelos embebidos como JSON para el JS del comparador."""
    return json.dumps(modelos, ensure_ascii=False, separators=(",", ":"))


def comparador_cuerpo(modelos, meta):
    """Cuerpo HTML del comparador interactivo."""

    opciones = "\n".join(
        f'<option value="{escape(m["slug"])}">{escape(m["nombre"])}</option>'
        for m in modelos
    )

    # pares sugeridos: mismo segmento o precios que se solapan
    sugeridos = []
    for i, a in enumerate(modelos):
        for b in modelos[i + 1:]:
            pa = _num(a.get("precio_desde"))
            pb = _num(b.get("precio_desde"))
            if pa is None or pb is None:
                continue
            mismo_seg = a.get("segmento") and a.get("segmento") == b.get("segmento")
            cerca = abs(pa - pb) / max(pa, pb) <= 0.25
            if mismo_seg or cerca:
                pares = sorted([a["slug"], b["slug"]])
                sugeridos.append((a["nombre"], b["nombre"], pares[0], pares[1]))

    sugeridos_html = "\n".join(
        f'<a class="cmp-sug" href="comparar/{u}-vs-{v}.html">{escape(n1)} vs {escape(n2)}</a>'
        for n1, n2, u, v in sugeridos[:24]
    )

    return f"""
<h1>Comparador de autos en Ecuador</h1>
<p class="lead">Elegi dos modelos y mira las fichas frente a frente. Los datos salen de las
fichas oficiales de cada marca y de AEADE. Cuando un fabricante no publica un dato,
la fila dice <em>No publicado</em> y no se compara: preferimos un hueco visible
antes que un numero inventado.</p>

<div class="cmp-panel">
  <div class="cmp-sel">
    <label for="cmp-a">Modelo A</label>
    <select id="cmp-a">{opciones}</select>
  </div>
  <div class="cmp-vs">vs</div>
  <div class="cmp-sel">
    <label for="cmp-b">Modelo B</label>
    <select id="cmp-b">{opciones}</select>
  </div>
</div>

<div id="cmp-veredicto" class="cmp-veredicto"></div>
<div id="cmp-tabla" class="cmp-tabla-wrap"><p class="cmp-vacio">Cargando…</p></div>

<h2>Comparaciones ya publicadas</h2>
<p class="lead">Analisis modelo contra modelo con el detalle de cada uno.</p>
<div class="cmp-sugerencias">
{sugeridos_html}
</div>
"""


def comparador_js(modelos):
    """JS del comparador. Autocontenido, sin dependencias."""
    return """
(function(){
  var MODELOS = __DATOS__;
  var CAMPOS = __CAMPOS__;
  var GRUPOS = __GRUPOS__;

  var porSlug = {};
  MODELOS.forEach(function(m){ porSlug[m.slug] = m; });

  function num(v){
    if(v===null||v===undefined||v==="") return null;
    if(typeof v === "number") return v;
    var n = parseFloat(String(v).replace(/[^0-9.\\-]/g,""));
    return isNaN(n) ? null : n;
  }

  function muestra(v, unidad){
    if(v===null||v===undefined||v==="") return null;
    if(Object.prototype.toString.call(v)==="[object Array]"){
      return v.length ? v.join(", ") : null;
    }
    if(unidad==="USD"){
      var n=num(v);
      if(n===null) return null;
      return "USD " + n.toLocaleString("es-EC");
    }
    if(typeof v === "number" && v % 1 === 0){
      return unidad ? (v + " " + unidad) : String(v);
    }
    return unidad ? (v + " " + unidad) : String(v);
  }

  function esc(s){
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  function pinta(){
    var a = porSlug[document.getElementById("cmp-a").value];
    var b = porSlug[document.getElementById("cmp-b").value];
    if(!a || !b) return;

    var victoriasA = 0, victoriasB = 0, comparables = 0;
    var grupoActual = null;
    var filas = "";

    CAMPOS.forEach(function(c){
      var clave=c[0], etiq=c[1], unidad=c[2], dir=c[3], grupo=c[4];
      var va = a[clave], vb = b[clave];
      var ma = muestra(va, unidad), mb = muestra(vb, unidad);
      // Si falta en AMBOS lados la fila no aporta: se omite.
      if(ma === null && mb === null) return;
      if(grupo !== grupoActual){
        grupoActual = grupo;
        filas += '<tr class="cmp-grupo"><td colspan="3">' + esc(GRUPOS[grupo]||grupo) + '</td></tr>';
      }
      var claseA = "", claseB = "", marca = "";

      if(dir){
        var na = num(va), nb = num(vb);
        if(na === null || nb === null){
          marca = '<span class="cmp-nc">no comparable</span>';
        } else if(na !== nb){
          comparables++;
          var ganaA = (dir === "menor") ? (na < nb) : (na > nb);
          if(ganaA){ victoriasA++; claseA = "cmp-mejor"; claseB = "cmp-peor"; }
          else     { victoriasB++; claseB = "cmp-mejor"; claseA = "cmp-peor"; }
        }
      }

      filas += '<tr><th>' + esc(etiq) + '</th>'
             + '<td class="' + claseA + '">' + (ma===null ? '<span class="cmp-np">No publicado</span>' : esc(ma)) + '</td>'
             + '<td class="' + claseB + '">' + (mb===null ? '<span class="cmp-np">No publicado</span>' : esc(mb)) + '</td>'
             + '</tr>';
    });

    var html = '<table class="cmp-tabla"><thead><tr><th></th>'
             + '<th>' + esc(a.nombre) + '</th><th>' + esc(b.nombre) + '</th>'
             + '</tr></thead><tbody>' + filas + '</tbody></table>';
    document.getElementById("cmp-tabla").innerHTML = html;

    var v = "";
    if(comparables === 0){
      v = '<p>No hay suficientes datos publicados para decidir entre estos dos modelos.</p>';
    } else if(victoriasA === victoriasB){
      v = '<p><strong>Empate tecnico</strong>: ' + victoriasA + ' a ' + victoriasB
        + ' en ' + comparables + ' datos comparables.</p>';
    } else {
      var gana = victoriasA > victoriasB ? a : b;
      var vict = Math.max(victoriasA, victoriasB);
      var pierde = Math.min(victoriasA, victoriasB);
      v = '<p><strong>' + esc(gana.nombre) + '</strong> gana en ' + vict + ' de '
        + comparables + ' datos comparables frente a ' + pierde + '.</p>'
        + '<p class="cmp-nota">Esto cuenta datos publicados, no es un veredicto de compra: '
        + 'pesa mas lo que a vos te importa (precio, consumo, seguridad, reventa).</p>';
    }
    document.getElementById("cmp-veredicto").innerHTML = v;

    // reflejar en la URL para poder compartir la comparacion
    var q = "?a=" + a.slug + "&b=" + b.slug;
    if(window.history && window.history.replaceState){
      window.history.replaceState(null, "", q);
    }
  }

  function init(){
    var selA = document.getElementById("cmp-a");
    var selB = document.getElementById("cmp-b");
    var params = new URLSearchParams(window.location.search);
    var qa = params.get("a"), qb = params.get("b");
    if(qa && porSlug[qa]) selA.value = qa;
    if(qb && porSlug[qb]) selB.value = qb;
    if(selA.value === selB.value && MODELOS.length > 1){
      for(var i=0;i<MODELOS.length;i++){
        if(MODELOS[i].slug !== selA.value){ selB.value = MODELOS[i].slug; break; }
      }
    }
    selA.addEventListener("change", pinta);
    selB.addEventListener("change", pinta);
    pinta();
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
"""


def comparador_css():
    """CSS del comparador. Usa la paleta del sitio con respaldo."""
    return """
.cmp-panel{display:flex;gap:12px;align-items:flex-end;background:var(--card,#151a20);
 border:1px solid var(--bd,#232b33);border-radius:12px;padding:16px;margin:18px 0;flex-wrap:wrap}
.cmp-sel{flex:1;min-width:180px}
.cmp-sel label{display:block;font-size:13px;color:var(--mut,#8d99a6);margin-bottom:6px}
.cmp-sel select{width:100%;padding:10px 12px;border-radius:8px;background:var(--bg,#0d0f12);
 color:var(--tx,#e8edf2);border:1px solid var(--bd,#232b33);font-size:15px}
.cmp-vs{color:var(--mut,#8d99a6);font-weight:700;padding-bottom:10px}
.cmp-veredicto{background:var(--card,#151a20);border-left:3px solid var(--acc,#e8b93b);
 border-radius:8px;padding:14px 16px;margin:16px 0}
.cmp-veredicto p{margin:0 0 6px}
.cmp-nota{color:var(--mut,#8d99a6);font-size:14px}
.cmp-tabla-wrap{overflow-x:auto;margin:18px 0}
.cmp-tabla{width:100%;border-collapse:collapse;font-size:15px}
.cmp-tabla th,.cmp-tabla td{padding:10px 12px;border-bottom:1px solid var(--bd,#232b33);
 text-align:left;vertical-align:top}
.cmp-tabla thead th{color:var(--acc,#e8b93b);font-size:14px;text-transform:uppercase;
 letter-spacing:.04em;border-bottom:2px solid var(--bd,#232b33)}
.cmp-tabla tbody th{color:var(--mut,#8d99a6);font-weight:400;width:38%}
.cmp-grupo td{background:var(--bg,#0d0f12);color:var(--acc,#e8b93b);font-weight:700;
 font-size:13px;text-transform:uppercase;letter-spacing:.06em;padding-top:16px}
.cmp-mejor{color:var(--acc2,#3ba55d);font-weight:700}
.cmp-peor{color:var(--mut,#8d99a6)}
.cmp-np{color:var(--mut,#8d99a6);font-style:italic;font-size:14px}
.cmp-nc{color:var(--mut,#8d99a6);font-size:12px;font-weight:400;font-style:italic}
.cmp-vacio{color:var(--mut,#8d99a6)}
.cmp-sugerencias{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.cmp-sug{display:inline-block;padding:8px 12px;border:1px solid var(--bd,#232b33);
 border-radius:8px;background:var(--card,#151a20);font-size:14px;color:var(--tx,#e8edf2)}
.cmp-sug:hover{border-color:var(--acc,#e8b93b);text-decoration:none}
"""


def _inyectar(js, modelos):
    campos = json.dumps([list(c) for c in CAMPOS], ensure_ascii=False, separators=(",", ":"))
    return (js
            .replace("__DATOS__", _js_datos(modelos))
            .replace("__CAMPOS__", campos)
            .replace("__GRUPOS__", json.dumps(GRUPOS, ensure_ascii=False, separators=(",", ":"))))


# ---------------------------------------------------------------------------
# 2. Pagina estatica por par
# ---------------------------------------------------------------------------

def par_cuerpo(a, b):
    """Cuerpo HTML de una pagina estatica modelo vs modelo."""
    filas = ""
    grupo_actual = None
    va_gana = vb_gana = 0

    for clave, etiq, unidad, direccion, grupo in CAMPOS:
        ma = _muestra(a.get(clave), unidad)
        mb = _muestra(b.get(clave), unidad)
        # Si el dato falta en AMBOS lados, la fila no aporta nada: se omite.
        if ma is None and mb is None:
            continue
        if grupo != grupo_actual:
            grupo_actual = grupo
            filas += f'<tr class="cmp-grupo"><td colspan="3">{escape(GRUPOS[grupo])}</td></tr>'
        ca = cb = ""
        if direccion:
            na, nb = _num(a.get(clave)), _num(b.get(clave))
            if na is not None and nb is not None and na != nb:
                gana_a = (na < nb) if direccion == "menor" else (na > nb)
                if gana_a:
                    va_gana += 1; ca, cb = "cmp-mejor", "cmp-peor"
                else:
                    vb_gana += 1; cb, ca = "cmp-mejor", "cmp-peor"
        ca_txt = escape(ma) if ma else '<span class="cmp-np">No publicado</span>'
        cb_txt = escape(mb) if mb else '<span class="cmp-np">No publicado</span>'
        filas += (f'<tr><th>{escape(etiq)}</th>'
                  f'<td class="{ca}">{ca_txt}</td>'
                  f'<td class="{cb}">{cb_txt}</td></tr>')

    total = va_gana + vb_gana
    if total == 0:
        veredicto = "<p>No hay suficientes datos publicados para decidir entre estos dos modelos.</p>"
    elif va_gana == vb_gana:
        veredicto = f"<p><strong>Empate tecnico</strong>: {va_gana} a {vb_gana} en {total} datos comparables.</p>"
    else:
        gana = a if va_gana > vb_gana else b
        vict, pierde = max(va_gana, vb_gana), min(va_gana, vb_gana)
        veredicto = (f"<p><strong>{escape(gana['nombre'])}</strong> gana en {vict} de {total} "
                     f"datos comparables frente a {pierde}.</p>"
                     '<p class="cmp-nota">Esto cuenta datos publicados, no es un veredicto de compra.</p>')

    nota_a = a.get("notas") or ""
    nota_b = b.get("notas") or ""

    return f"""
<h1>{escape(a['nombre'])} vs {escape(b['nombre'])}: comparacion en Ecuador</h1>
<p class="lead">Precio, motor, consumo y seguridad de los dos modelos, lado a lado, con los
datos publicados por cada fabricante para el mercado ecuatoriano. Las filas donde falta
un dato lo dicen en vez de estimarlo.</p>

<div class="cmp-veredicto">{veredicto}</div>

<div class="cmp-tabla-wrap">
<table class="cmp-tabla">
<thead><tr><th></th><th>{escape(a['nombre'])}</th><th>{escape(b['nombre'])}</th></tr></thead>
<tbody>{filas}</tbody>
</table>
</div>

<h2>Que dice cada ficha</h2>
<p><strong>{escape(a['nombre'])}:</strong> {escape(nota_a) or 'Sin nota del fabricante.'}</p>
<p><strong>{escape(b['nombre'])}:</strong> {escape(nota_b) or 'Sin nota del fabricante.'}</p>

<p class="cmp-nota">Podes armar otras combinaciones en el
<a href="../comparador.html">comparador interactivo</a>.</p>
"""


def modelos_documentados(modelos, minimo=MINIMO_DATOS):
    """
    Separa los modelos que tienen datos suficientes de los que no.

    Un modelo con pocos campos produce comparaciones tipo "gana 1 de 2",
    que es contenido vacio. Esos modelos se excluyen del comparador
    (siguen existiendo en modelos.json y en sus propias paginas de analisis).
    """
    completos, flojos = [], []
    for m in modelos:
        n = sum(1 for c in CAMPOS_CLAVE if m.get(c) not in (None, "", [], 0))
        (completos if n >= minimo else flojos).append((m, n))
    return completos, flojos


def generar_todo(raiz=".", paginas=None):
    """
    Genera comparador.html y las paginas de pares.
    `paginas` es la funcion pagina() de build.py (titulo, descripcion, cuerpo, ...).
    Devuelve (numero_de_archivos, lista_de_rutas).
    """
    todos, meta = cargar_modelos(os.path.join(raiz, "data", "modelos.json"))
    escritos = []

    completos, flojos = modelos_documentados(todos)
    modelos = [m for m, _ in completos]

    print(f"    comparador: {len(modelos)} modelos con datos suficientes "
          f"(minimo {MINIMO_DATOS} de {len(CAMPOS_CLAVE)} campos)")
    if flojos:
        print(f"    excluidos por falta de datos ({len(flojos)}):")
        for m, n in sorted(flojos, key=lambda x: -x[1]):
            faltan = [c for c in CAMPOS_CLAVE if m.get(c) in (None, "", [], 0)]
            print(f"       {m['nombre'][:24]:25} {n}/{len(CAMPOS_CLAVE)}  "
                  f"falta: {', '.join(faltan[:4])}{'...' if len(faltan) > 4 else ''}")

    if paginas is None:
        raise ValueError("hay que pasar la funcion pagina() de build.py")

    # --- comparador interactivo ---
    cuerpo = comparador_cuerpo(modelos, meta)
    html = paginas(
        "Comparador de autos en Ecuador: elige dos modelos y compara",
        "Compara precio, motor, consumo y seguridad de los autos mas vendidos de Ecuador. "
        "Datos oficiales, lado a lado, con los huecos visibles en vez de estimaciones.",
        cuerpo,
        ruta_rel="",
        canonical="https://cuantocuesta.xyz/comparador.html",
        schema=[],
    )
    html = html.replace("</head>", f"<style>{comparador_css()}</style>\n</head>")
    html = html.replace("</body>", f"<script>{_inyectar(comparador_js(modelos), modelos)}</script>\n</body>")
    ruta = os.path.join(raiz, "dist", "comparador.html")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    escritos.append("comparador.html")

    # --- paginas estaticas por par ---
    pares = []
    for i, a in enumerate(modelos):
        for b in modelos[i + 1:]:
            pa, pb = _num(a.get("precio_desde")), _num(b.get("precio_desde"))
            if pa is None or pb is None:
                continue
            mismo_seg = a.get("segmento") and a.get("segmento") == b.get("segmento")
            cerca = abs(pa - pb) / max(pa, pb) <= 0.30
            if mismo_seg or cerca:
                pares.append((a, b))

    for a, b in pares:
        slug = f"{a['slug']}-vs-{b['slug']}"
        html = paginas(
            f"{a['nombre']} vs {b['nombre']}: precio, consumo y seguridad en Ecuador",
            f"Comparacion entre {a['nombre']} y {b['nombre']} en Ecuador: precio, motor, "
            f"consumo declarado, seguridad y garantia, lado a lado.",
            par_cuerpo(a, b),
            ruta_rel="../",
            canonical=f"https://cuantocuesta.xyz/comparar/{slug}.html",
            schema=[],
        )
        html = html.replace("</head>", f"<style>{comparador_css()}</style>\n</head>")
        ruta = os.path.join(raiz, "dist", "comparar", f"{slug}.html")
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)
        escritos.append(f"comparar/{slug}.html")

    return len(escritos), escritos


if __name__ == "__main__":
    modelos, meta = cargar_modelos()
    print(f"modelos: {len(modelos)}")
    campos = sum(1 for c in CAMPOS if c[3])
    print(f"campos comparables: {campos} de {len(CAMPOS)}")
    print(f"grupos: {', '.join(GRUPOS)}")
    faltantes = {}
    for m in modelos:
        for c in CAMPOS:
            if c[3] and (m.get(c[0]) is None or m.get(c[0]) == ""):
                faltantes[c[1]] = faltantes.get(c[1], 0) + 1
    print("\ndatos faltantes por campo (se mostraran como 'No publicado'):")
    for k, v in sorted(faltantes.items(), key=lambda x: -x[1]):
        print(f"  {v:2} de {len(modelos)}  {k}")
