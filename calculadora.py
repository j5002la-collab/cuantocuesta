#!/usr/bin/env python3
"""
Calculadora interactiva de costo de mantener un auto en Ecuador.

Es el activo de posicionamiento del sitio: una herramienta real que
nadie más tiene en Ecuador y que atrae enlaces naturales.

Genera dist/calculadora.html — todo en un archivo, sin dependencias.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build import (SITIO, CSS, DIST, ASSETS)  # noqa: E402

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# datos base por modelo: (nombre, precio, consumo_km_l, cilindraje_cc, combustible)
# combustible: 'extra' | 'super' | 'diesel'
MODELOS = [
    ("Kia Soluto", 16990, 19.3, 1400, "extra"),
    ("Kia Sonet", 21990, 16.0, 1500, "extra"),
    ("Kia Seltos", 27990, 14.5, 1500, "extra"),
    ("Kia Sportage", 37990, 12.0, 2000, "extra"),
    ("Hyundai Grand i10", 15990, 17.5, 1200, "extra"),
    ("Hyundai Creta", 26490, 15.0, 1500, "extra"),
    ("Hyundai Tucson", 42990, 11.5, 2000, "extra"),
    ("Chevrolet Groove", 19990, 15.0, 1500, "extra"),
    ("Chevrolet D-Max", 34990, 10.5, 2500, "diesel"),
    ("Chery Arrizo", 17990, 15.5, 1500, "extra"),
    ("GWM Poer", 32990, 10.0, 2000, "diesel"),
    ("Toyota Hilux", 38990, 11.0, 2400, "diesel"),
    ("Eléctrico compacto", 32000, 0, 0, "electrico"),
    ("Eléctrico SUV", 45000, 0, 0, "electrico"),
]

# precios vigentes en Ecuador (Petroecuador, 12 sep - 11 oct 2026)
PRECIOS = {"extra": 3.212, "super": 4.89, "diesel": 3.151}
ETIQUETA = {"extra": "Extra / Ecopaís (85 oct)",
            "super": "Súper (95 oct)",
            "diesel": "Diésel Premium"}

# Capacidad de tanque: SOLO datos verificados de data/tanques.json.
# Si un modelo no tiene dato, la calculadora no muestra esa seccion.
TANQUES_BASE = {}
DATOS_FUENTE = {}
try:
    _raw = json.loads((DATA_DIR / "tanques.json").read_text(encoding="utf-8"))
    for _modelo, _d in (_raw.get("valores") or {}).items():
        if _d.get("tanque_l"):
            TANQUES_BASE[_modelo] = _d["tanque_l"]
        DATOS_FUENTE[_modelo] = {
            "fuente": _d.get("fuente", ""),
            "consumo_km_l": _d.get("consumo_km_l"),
            "consumo_km_galon": _d.get("consumo_km_galon"),
            "fuente_consumo": _d.get("fuente_consumo", ""),
            "octanaje": _d.get("octanaje", ""),
            "confianza": _d.get("confianza", ""),
        }
except Exception as _e:
    print(f"  aviso: no se pudo leer data/tanques.json: {_e}")


def generar_calculadora():
    html = """<a class="volver" href="index.html">← Inicio</a>
<h1>Calculadora: cuánto cuesta mantener un auto en Ecuador</h1>
<p class="lead">Elige tu auto, pon tus kilómetros reales y mira el desglose mes a mes.
Los valores se calculan con las tarifas vigentes del SRI, la ANT y los precios de
combustible de Petroecuador. Cambia cualquier dato y el resultado se actualiza al instante.</p>

<form class="calc" id="calc" onsubmit="return false">
  <div class="calc-fila">
    <label for="modelo">Modelo</label>
    <select id="modelo"></select>
  </div>
  <div class="calc-fila">
    <label for="km">Kilómetros al mes</label>
    <input type="number" id="km" value="1000" min="100" max="8000" step="50">
  </div>
  <div class="calc-fila">
    <label for="tipo_comb">Combustible</label>
    <select id="tipo_comb">
      <option value="auto">El que recomienda el modelo</option>
      <option value="extra">Extra / Ecopaís: $3,212</option>
      <option value="super">Súper: $4,89</option>
      <option value="diesel">Diésel Premium: $3,151</option>
    </select>
  </div>
  <div class="calc-fila">
    <label for="precio_comb">Precio por galón (USD)</label>
    <input type="number" id="precio_comb" value="3.212" min="1" max="8" step="0.001">
  </div>
  <div class="calc-fila">
    <label for="ciudad">Ciudad (afecta revisión técnica)</label>
    <select id="ciudad">
      <option value="1.0">Quito</option>
      <option value="0.95">Guayaquil</option>
      <option value="0.92">Cuenca</option>
      <option value="0.90">Otra ciudad</option>
    </select>
  </div>
  <div class="calc-fila">
    <label>Tipo de uso</label>
    <div class="calc-radios">
      <label><input type="radio" name="uso" value="1.0" checked> Mixto</label>
      <label><input type="radio" name="uso" value="1.12"> Ciudad (tráfico)</label>
      <label><input type="radio" name="uso" value="0.92"> Carretera</label>
    </div>
  </div>
  <div class="calc-fila">
    <label>Tipo de seguro</label>
    <div class="calc-radios">
      <label><input type="radio" name="seguro" value="0" checked> Solo SPPAT</label>
      <label><input type="radio" name="seguro" value="0.035"> Todo riesgo 3,5%</label>
      <label><input type="radio" name="seguro" value="0.055"> Todo riesgo 5,5%</label>
    </div>
  </div>
</form>

<div class="calc-res">
  <div class="calc-total">
    <span class="etiqueta">Costo mensual estimado</span>
    <span id="total">$0</span>
  </div>
  <div class="calc-total calc-anual">
    <span class="etiqueta">Al año</span>
    <span id="anual">$0</span>
  </div>
  <div class="calc-total calc-km">
    <span class="etiqueta">Por kilómetro</span>
    <span id="porkm">$0</span>
  </div>
</div>

<h2>Tanque y rendimiento del modelo elegido</h2>
<div class="calc-res" id="tanque-res"></div>

<h2>Desglose mensual</h2>
<table class="calc-tabla" id="tabla">
  <thead><tr><th>Concepto</th><th>Cómo se calcula</th><th>Mensual</th></tr></thead>
  <tbody></tbody>
</table>

<div class="destacado">
<h3>Cómo interpretar el resultado</h3>
<p><strong>Combustible</strong> es el rubro que más varía: depende de tu pie real, no del consumo
declarado por el fabricante. Bajar de 1.200 a 900 km al mes puede ahorrarte más que cambiar de auto.</p>
<p><strong>Extra o Súper</strong> es la decisión de costo operativo más grande que existe. La Súper
cuesta <strong>52% más</strong> por galón ($4,89 contra $3,212). Revisa el manual: si tu versión
admite Extra, usarla te ahorra cientos de dólares al año.</p>
<p><strong>Seguro y matrícula</strong> son costos fijos anuales que aquí se prorratean. Si pagas
todo riesgo, es el segundo rubro más pesado después del combustible.</p>
</div>

<h2>Precios de combustible usados</h2>
<table class="calc-tabla">
<thead><tr><th>Tipo</th><th>Octanaje</th><th>Precio por galón</th><th>Vigencia</th></tr></thead>
<tbody>
<tr><td>Extra</td><td>85</td><td class="num">$3,212</td><td>12 sep – 11 oct 2026</td></tr>
<tr><td>Ecopaís</td><td>85</td><td class="num">$3,212</td><td>12 sep – 11 oct 2026</td></tr>
<tr><td>Súper</td><td>95</td><td class="num">$4,89 (sugerido)</td><td>liberado, varía por estación</td></tr>
<tr><td>Diésel Premium</td><td>—</td><td class="num">$3,151</td><td>12 sep – 11 oct 2026</td></tr>
</tbody>
</table>
<p class="meta">Precios regulados por Petroecuador. La Súper no tiene subsidio desde 2018 y su
precio es liberado: el valor final depende de cada estación (por ejemplo, Primax suele venderla
por encima del sugerido). Fuente: Petroecuador y Decreto 468.</p>

<h2>Unidad que usa esta calculadora</h2>
<p class="meta">En Ecuador el combustible se vende por <strong>galón</strong>, no por litro:
1 galón = 3,785 litros. Los rendimientos se muestran en km por galón y en km por litro para que
puedas comparar con la ficha de tu modelo, que puede venir en cualquiera de las dos unidades.</p>

<script>
const MODELOS = """ + str([list(m) for m in MODELOS]).replace("'", '"') + """;
const PRECIOS = """ + str(PRECIOS).replace("'", '"') + """;
const ETIQUETA = """ + str(ETIQUETA).replace("'", '"') + """;
window.TANQUES = """ + json.dumps(TANQUES_BASE, ensure_ascii=False) + """;

const sel = document.getElementById('modelo');
MODELOS.forEach((m, i) => {
  const o = document.createElement('option');
  o.value = i;
  o.textContent = m[0];
  sel.appendChild(o);
});

function fmt(n) {
  return '$' + n.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
}

function calcular() {
  const m = MODELOS[sel.value];
  const [nombre, precio, kml, cc, tipoBase] = m;
  const km = +document.getElementById('km').value || 1000;
  const ciudad = +document.getElementById('ciudad').value;
  const uso = +document.querySelector('input[name=uso]:checked').value;
  const pSeguro = +document.querySelector('input[name=seguro]:checked').value;
  const elegido = document.getElementById('tipo_comb').value;
  const tipo = elegido === 'auto' ? tipoBase : elegido;

  const esElectrico = tipoBase === 'electrico';
  const filas = [];
  let pComb = +document.getElementById('precio_comb').value || PRECIOS[tipo] || 3.212;

  // si el usuario no toco el precio, usar el vigente del tipo elegido
  if (elegido !== 'auto' && document.getElementById('precio_comb').dataset.auto !== 'no') {
    pComb = PRECIOS[tipo];
    document.getElementById('precio_comb').value = pComb.toFixed(3);
  }

  if (esElectrico) {
    const kwh = km * 0.18 * uso;
    const costo = kwh * 0.10;
    filas.push(['Electricidad', (kwh.toFixed(0) + ' kWh × $0,10'), costo]);
    pComb = 0;
  } else {
    const litros = (km * uso) / kml;
    const galones = litros / 3.785;
    const costo = galones * pComb;
    filas.push(['Combustible (' + (ETIQUETA[tipo] || tipo) + ')',
      (litros.toFixed(0) + ' L = ' + galones.toFixed(1) + ' gal × ' + fmt(pComb)), costo]);
  }

  let matriculaAnual;
  if (esElectrico) matriculaAnual = 120;
  else if (cc <= 1500) matriculaAnual = 220;
  else if (cc <= 2000) matriculaAnual = 290;
  else if (cc <= 2500) matriculaAnual = 420;
  else matriculaAnual = 560;
  filas.push(['Matrícula y rodaje', 'rubros SRI y ANT ÷ 12', matriculaAnual / 12]);

  const sppat = esElectrico ? 60 : (cc <= 1500 ? 95 : 135);
  let costoSe = sppat / 12;
  let descSeguro = 'SPPAT ÷ 12';
  if (pSeguro > 0) {
    costoSe = (precio * pSeguro) / 12 + sppat / 12;
    descSeguro = ((pSeguro * 100).toFixed(1) + '% del valor + SPPAT');
  }
  filas.push(['Seguro', descSeguro, costoSe]);

  const mantAnual = esElectrico ? (km / 5000) * 45 : (km / 5000) * 120;
  filas.push(['Mantenimiento', 'cada 5.000 km', mantAnual / 12]);

  const rev = 45 * ciudad;
  filas.push(['Revisión técnica', 'según ciudad ÷ 12', rev / 12]);

  const total = filas.reduce((a, f) => a + f[2], 0);
  const tbody = document.querySelector('#tabla tbody');
  tbody.innerHTML = filas.map(f =>
    '<tr><td>' + f[0] + '</td><td class="calc-desc">' + f[1] + '</td><td class="num">' + fmt(f[2]) + '</td></tr>'
  ).join('') + '<tr class="calc-sum"><td>Total</td><td></td><td class="num">' + fmt(total) + '</td></tr>';

  document.getElementById('total').textContent = fmt(total);
  document.getElementById('anual').textContent = fmt(total * 12);
  document.getElementById('porkm').textContent = '$' + (total / km).toFixed(3);

  // tanque y rendimiento del modelo
  const kmGal = kml > 0 ? kml * 3.785 : 0;
  const tanqueL = window.TANQUES ? window.TANQUES[nombre] : null;
  const tanqueG = tanqueL ? tanqueL / 3.785 : null;
  let tr = '';
  if (tanqueL) {
    tr += '<div class="calc-total"><span class="etiqueta">Tanque de combustible</span><span>' +
          tanqueL + ' L</span></div>';
    tr += '<div class="calc-total calc-anual"><span class="etiqueta">Equivale a</span><span>' +
          tanqueG.toFixed(1) + ' gal</span></div>';
    if (!esElectrico && pComb > 0) {
      tr += '<div class="calc-total calc-km"><span class="etiqueta">Llenar el tanque cuesta</span><span>' +
            fmt(tanqueG * pComb) + '</span></div>';
    }
  }
  if (!esElectrico) {
    tr += '<div class="calc-total"><span class="etiqueta">Rendimiento</span><span>' +
          kml.toFixed(1) + ' km/l</span></div>';
    tr += '<div class="calc-total calc-anual"><span class="etiqueta">Equivale a</span><span>' +
          kmGal.toFixed(0) + ' km/gal</span></div>';
  }
  if (tr) {
    document.getElementById('tanque-res').innerHTML = tr;
    document.getElementById('tanque-res').style.display = 'grid';
  } else {
    document.getElementById('tanque-res').style.display = 'none';
  }

  const p = new URLSearchParams({
    m: sel.value, km: km, comb: pComb.toFixed(3), ciu: document.getElementById('ciudad').value
  });
  history.replaceState(null, '', '?' + p.toString());
}

document.getElementById('precio_comb').dataset.auto = 'si';
document.getElementById('tipo_comb').addEventListener('change', function () {
  const t = this.value;
  document.getElementById('precio_comb').dataset.auto = t === 'auto' ? 'si' : 'no';
  if (t !== 'auto') document.getElementById('precio_comb').value = PRECIOS[t].toFixed(3);
  calcular();
});
document.querySelectorAll('#calc select, #calc input').forEach(el => {
  if (el.id === 'tipo_comb') return;
  el.addEventListener('change', calcular);
  el.addEventListener('input', function () {
    if (this.id === 'precio_comb') this.dataset.auto = 'no';
    calcular();
  });
});

const q = new URLSearchParams(location.search);
if (q.get('m')) sel.value = q.get('m');
if (q.get('km')) document.getElementById('km').value = q.get('km');
if (q.get('comb')) {
  document.getElementById('precio_comb').value = q.get('comb');
  document.getElementById('precio_comb').dataset.auto = 'no';
}
if (q.get('ciu')) document.getElementById('ciudad').value = q.get('ciu');

calcular();
</script>

<h2 id="preguntas">Preguntas frecuentes</h2>

<div class="faq">
<details open>
<summary>¿Cuánto cuesta mantener un auto en Ecuador al mes?</summary>
<p>Depende de tres cosas: el valor del vehículo, los kilómetros que hagas y el seguro que
elijas. Un sedán compacto de alrededor de <strong>$16.000</strong> con 1.000 km al mes
suele costar entre <strong>$110 y $150 mensuales</strong> sumando combustible, matrícula,
seguro y mantenimiento. Una camioneta de <strong>$38.000</strong> con el mismo uso pasa
fácilmente de <strong>$300</strong>. Usa la calculadora de arriba con tus datos reales
para ver tu caso.</p>
</details>

<details>
<summary>¿Qué cuesta más: la gasolina o el mantenimiento?</summary>
<p>El combustible se lleva entre el <strong>45% y el 60%</strong> del costo total en la
mayoría de los casos. El mantenimiento preventivo (aceite, filtros, frenos, llantas) pesa
entre el <strong>15% y el 25%</strong>. La matrícula y la revisión técnica son fijas y no
dependen de cuánto manejes, así que en un auto de poco uso suben de peso proporcional.</p>
</details>

<details>
<summary>¿Conviene más un diésel o un gasolina?</summary>
<p>El diésel rinde más kilómetros por galón y el galón cuesta menos, así que en kilometraje
alto gana. El problema es el mantenimiento: los inyectores y el sistema de alta presión
son más caros de reparar y exigen aceite y filtros de especificación más estricta. El
punto de equilibrio suele estar alrededor de <strong>25.000 km al año</strong>. Por
debajo de eso, el gasolina sale más barato de operar y de reparar.</p>
</details>

<details>
<summary>¿Cuánto sube el costo si manejo en Quito en vez de Guayaquil?</summary>
<p>Quito pesa más por el tráfico y las pendientes: el consumo por kilómetro sube entre
<strong>10% y 15%</strong>. Guayaquil compensa en parte con el aire acondicionado, que
también consume. La revisión técnica también cambia de precio según el cantón. La
calculadora ya aplica ese ajuste cuando eliges la ciudad.</p>
</details>

<details>
<summary>¿Vale la pena el seguro todo riesgo en un auto nuevo?</summary>
<p>En un vehículo de menos de cinco años, casi siempre sí: el todo riesgo cuesta entre el
<strong>3% y el 5% del valor</strong> al año, y una sola reparación de carrocería puede
superar esa prima. En un auto viejo de bajo valor, el cálculo se invierte y muchas veces
conviene quedarse con una cobertura básica. El umbral práctico está alrededor de
<strong>$12.000</strong> de valor comercial.</p>
</details>

<details>
<summary>¿Los datos de esta calculadora de dónde salen?</summary>
<p>El combustible usa los precios regulados de Petroecuador con su fecha de vigencia. La
matrícula y la revisión técnica usan los tarifarios del SRI y de la ANT. El rendimiento
de cada modelo sale de la ficha técnica oficial del fabricante cuando está publicada. Si
un dato no está publicado, la calculadora lo dice en vez de estimarlo. Los precios de los
combustibles cambian cada mes: revisa la tabla de vigencia que está abajo.</p>
</details>
</div>

<h2 id="como-funciona">Cómo se calcula</h2>
<p>El resultado se arma en cuatro bloques, y cada uno usa una fuente distinta:</p>
<ul>
<li><strong>Combustible:</strong> kilómetros al mes divididos por el rendimiento del modelo,
multiplicado por el precio del galón. Si el modelo no tiene rendimiento publicado, se usa
el promedio de su segmento y el resultado lo advierte.</li>
<li><strong>Matrícula y revisión técnica:</strong> tarifarios vigentes del SRI y la ANT,
con el ajuste por cantón cuando corresponde.</li>
<li><strong>Seguro:</strong> prima anual estimada como porcentaje del valor del vehículo,
que es como lo cotizan las aseguradoras ecuatorianas.</li>
<li><strong>Mantenimiento:</strong> el plan de servicio del fabricante por kilometraje
(aceite, filtros, frenos, llantas) más una reserva para imprevistos.</li>
</ul>
<p>Todo se expresa en costo mensual y anual, y también en <strong>costo por kilómetro</strong>,
que es la cifra que sirve para comparar dos autos de precio distinto.</p>

<h2 id="guias">Guías relacionadas</h2>
<p>Si quieres el detalle de cada rubro por separado:</p>
<ul>
<li><a href="costos-mantenimiento-por-marca-ecuador.html">Cuánto cuesta mantener un auto por marca en Ecuador</a></li>
<li><a href="top-10-cuanto-cuesta-mantener-auto-ecuador.html">Los 10 modelos más vendidos y lo que cuesta mantenerlos</a></li>
<li><a href="costo-por-kilometro-electrico-vs-gasolina-ecuador.html">Costo por kilómetro: eléctrico contra gasolina</a></li>
<li><a href="cuanto-cuesta-seguro-todo-riesgo-ecuador.html">Cuánto cuesta el seguro todo riesgo en Ecuador</a></li>
<li><a href="matricula-vehicular-ecuador-2026-costos-requisitos.html">Matrícula vehicular 2026: costos y requisitos</a></li>
<li><a href="revision-tecnica-vehicular-ecuador-guia.html">Revisión técnica vehicular: guía completa</a></li>
</ul>
"""

    return html


CSS_CALC = """
.calc{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin:26px 0}
.calc-fila{display:flex;flex-wrap:wrap;align-items:center;gap:14px;padding:11px 0;border-bottom:1px solid var(--bd)}
.calc-fila:last-child{border-bottom:0}
.calc-fila > label{flex:0 0 210px;color:var(--tx);font-size:.92rem}
.calc select,.calc input[type=number]{background:#0e1116;color:var(--tx);border:1px solid var(--bd);
  border-radius:7px;padding:9px 12px;font-size:.95rem;font-family:inherit;min-width:150px}
.calc input[type=file]{color:var(--mut)}
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
@media(max-width:640px){.calc-fila > label{flex:1 1 100%}.calc select,.calc input[type=number]{width:100%}}
.faq{margin:20px 0}
.faq details{background:var(--card);border:1px solid var(--bd);border-radius:10px;
  padding:14px 18px;margin-bottom:10px}
.faq details[open]{border-color:#3a4550}
.faq summary{cursor:pointer;color:var(--tx);font-weight:600;font-size:.97rem;line-height:1.45;
  list-style:none;display:flex;justify-content:space-between;align-items:flex-start;gap:14px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";color:var(--acc);font-weight:700;font-size:1.3rem;
  line-height:1;flex:0 0 auto}
.faq details[open] summary::after{content:"–"}
.faq summary:hover{color:var(--acc)}
.faq details p{margin:11px 0 2px;color:var(--mut);font-size:.93rem;line-height:1.68}
.faq details strong{color:var(--tx)}
"""


def _faq_schema():
    """JSON-LD FAQPage con las MISMAS preguntas y respuestas que se ven en la pagina.

    Regla de Google: el contenido del schema tiene que coincidir con el contenido
    visible. Si el schema trae preguntas que no estan en la pagina, lo marca como
    spam de datos estructurados. Por eso las dos listas viven juntas aqui abajo.
    """
    import json

    faq = [
        ("¿Cuánto cuesta mantener un auto en Ecuador al mes?",
         "Depende del valor del vehículo, los kilómetros que hagas y el seguro que elijas. "
         "Un sedán compacto de alrededor de $16.000 con 1.000 km al mes suele costar entre "
         "$110 y $150 mensuales sumando combustible, matrícula, seguro y mantenimiento. "
         "Una camioneta de $38.000 con el mismo uso pasa fácilmente de $300."),
        ("¿Qué cuesta más: la gasolina o el mantenimiento?",
         "El combustible se lleva entre el 45% y el 60% del costo total en la mayoría de los "
         "casos. El mantenimiento preventivo (aceite, filtros, frenos, llantas) pesa entre el "
         "15% y el 25%. La matrícula y la revisión técnica son fijas y no dependen de cuánto "
         "manejes, así que en un auto de poco uso suben de peso proporcional."),
        ("¿Conviene más un diésel o un gasolina?",
         "El diésel rinde más kilómetros por galón y el galón cuesta menos, así que en "
         "kilometraje alto gana. El problema es el mantenimiento: los inyectores y el sistema "
         "de alta presión son más caros de reparar y exigen aceite y filtros de "
         "especificación más estricta. El punto de equilibrio suele estar alrededor de "
         "25.000 km al año."),
        ("¿Cuánto sube el costo si manejo en Quito en vez de Guayaquil?",
         "Quito pesa más por el tráfico y las pendientes: el consumo por kilómetro sube entre "
         "10% y 15%. Guayaquil compensa en parte con el aire acondicionado, que también "
         "consume. La revisión técnica también cambia de precio según el cantón."),
        ("¿Vale la pena el seguro todo riesgo en un auto nuevo?",
         "En un vehículo de menos de cinco años, casi siempre sí: el todo riesgo cuesta entre "
         "el 3% y el 5% del valor al año, y una sola reparación de carrocería puede superar "
         "esa prima. En un auto viejo de bajo valor conviene una cobertura básica. El umbral "
         "práctico está alrededor de $12.000 de valor comercial."),
        ("¿Los datos de esta calculadora de dónde salen?",
         "El combustible usa los precios regulados de Petroecuador con su fecha de vigencia. "
         "La matrícula y la revisión técnica usan los tarifarios del SRI y de la ANT. El "
         "rendimiento de cada modelo sale de la ficha técnica oficial del fabricante cuando "
         "está publicada. Si un dato no está publicado, la calculadora lo dice en vez de "
         "estimarlo."),
    ]
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question",
             "name": p,
             "acceptedAnswer": {"@type": "Answer", "text": r}}
            for p, r in faq
        ],
    }, ensure_ascii=False)


def main():
    from build import pagina, schema_coleccion
    cuerpo = generar_calculadora()
    html = pagina(
        "Calculadora: costo de mantener un auto en Ecuador",
        "Calcula cuánto cuesta al mes mantener tu auto en Ecuador: combustible, matrícula, "
        "seguro y mantenimiento. Con tarifas SRI y ANT vigentes.",
        cuerpo,
        canonical=f"{SITIO['url']}/calculadora.html",
        schema=[
            '{"@context":"https://schema.org","@type":"WebApplication",'
            '"name":"Calculadora de costo de mantener un auto en Ecuador",'
            '"url":"' + SITIO["url"] + '/calculadora.html",'
            '"applicationCategory":"FinanceApplication",'
            '"operatingSystem":"Web",'
            '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},'
            '"description":"Calcula el costo mensual de mantener un auto en Ecuador con las tarifas del SRI y la ANT.",'
            '"inLanguage":"es-EC"}',
            '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
            '{"@type":"ListItem","position":1,"name":"Inicio","item":"' + SITIO["url"] + '/"},'
            '{"@type":"ListItem","position":2,"name":"Calculadora","item":"' + SITIO["url"] + '/calculadora.html"}]}',
            # FAQPage: esto es lo que puede producir resultado enriquecido en Google.
            # Las preguntas y respuestas tienen que coincidir EXACTAMENTE con las que
            # se ven en la pagina, o Google lo marca como spam de schema.
            _faq_schema(),
        ],
    )
    (DIST / "calculadora.html").write_text(html, encoding="utf-8")
    print("  ✓ calculadora.html")


if __name__ == "__main__":
    main()
