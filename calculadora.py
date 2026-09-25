#!/usr/bin/env python3
"""
Calculadora interactiva de costo de mantener un auto en Ecuador.

Es el activo de posicionamiento del sitio: una herramienta real que
nadie más tiene en Ecuador y que atrae enlaces naturales.

Genera dist/calculadora.html — todo en un archivo, sin dependencias.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build import (SITIO, CSS, DIST, ASSETS)  # noqa: E402

# datos base por modelo: (precio, consumo_km_l, cilindraje_cc)
MODELOS = [
    ("Kia Soluto", 16990, 15.5, 1400),
    ("Kia Sonet", 21990, 14.0, 1500),
    ("Kia Seltos", 27990, 13.0, 1500),
    ("Kia Sportage", 37990, 11.0, 2000),
    ("Hyundai Grand i10", 15990, 16.5, 1200),
    ("Hyundai Creta", 26490, 13.5, 1500),
    ("Hyundai Tucson", 42990, 10.5, 2000),
    ("Chevrolet Groove", 19990, 13.5, 1500),
    ("Chevrolet D-Max", 34990, 10.0, 2500),
    ("Chery Arrizo", 17990, 14.5, 1500),
    ("GWM Poer", 32990, 9.5, 2000),
    ("Toyota Hilux", 38990, 10.5, 2400),
    ("Eléctrico compacto", 32000, 0, 0),
    ("Eléctrico SUV", 45000, 0, 0),
]


def generar_calculadora():
    html = """<a class="volver" href="index.html">← Inicio</a>
<h1>Calculadora: cuánto cuesta mantener un auto en Ecuador</h1>
<p class="lead">Elige tu auto, pon tus kilómetros reales y mira el desglose mes a mes.
Los valores se calculan con las tarifas vigentes del SRI, ANT y el precio actual de
combustible. Cambia cualquier dato y el resultado se actualiza al instante.</p>

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
    <label for="precio_comb">Precio del galón (USD)</label>
    <input type="number" id="precio_comb" value="2.40" min="1" max="6" step="0.05"
           data-tipo="extra" data-clase="Ec">
  </div>
  <div class="calc-fila">
    <label for="ciudad">Ciudad (afecta revisión y seguro)</label>
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

<h2>Desglose mensual</h2>
<table class="calc-tabla" id="tabla">
  <thead><tr><th>Concepto</th><th>Cómo se calcula</th><th>Mensual</th></tr></thead>
  <tbody></tbody>
</table>

<div class="destacado">
<h3>Cómo interpretar el resultado</h3>
<p><strong>Combustible</strong> es el rubro que más varía: depende de tu pie real, no del consumo
declarado por el fabricante. Bajar de 1.200 a 900 km al mes puede ahorrarte más que cambiar de auto.</p>
<p><strong>Seguro y matrícula</strong> son costos fijos anuales que aquí se prorratean. Si pagas
todo riesgo, es el segundo rubro más pesado después del combustible.</p>
<p><strong>Mantenimiento preventivo</strong> se calcula por kilómetro recorrido: se acumula en el
tiempo aunque no lo notes mes a mes.</p>
</div>

<h2>Batería de datos que usa esta calculadora</h2>
<ul class="legal">
<li><strong>Combustible:</strong> extra a """ + "$2,40" + """ el galón (precio de referencia vigente).
Un galón equivale a 4,546 litros.</li>
<li><strong>Matrícula:</strong> rubros del SRI y la ANT, prorrateados en 12 meses según el
cilindraje del vehículo.</li>
<li><strong>Seguro:</strong> SPPAT obligatorio incluido en todo caso. El todo riesgo se estima
como porcentaje del valor del auto (3,5% a 5,5% anual en Ecuador).</li>
<li><strong>Mantenimiento:</strong> aceite, filtros y revisión periódica según tarifarios de
talleres autorizados, por cada 5.000 km.</li>
<li><strong>Revisión técnica:</strong> según ciudad, con su frecuencia real (Quito exige revisión
más seguida que otras ciudades).</li>
</ul>

<p class="meta">Los valores son referenciales. Las tasas municipales varían entre cantones, el
precio del seguro depende de tu historial y las promociones de taller son temporales. Verifica
siempre antes de decidir.</p>

<script>
const MODELOS = """ + str(MODELOS).replace("(", "[").replace(")", "]").replace("'", '"') + """;

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
  const [nombre, precio, kml, cc] = m;
  const km = +document.getElementById('km').value || 1000;
  const pComb = +document.getElementById('precio_comb').value || 2.40;
  const ciudad = +document.getElementById('ciudad').value;
  const uso = +document.querySelector('input[name=uso]:checked').value;
  const pSeguro = +document.querySelector('input[name=seguro]:checked').value;

  const esElectrico = kml === 0;
  const filas = [];

  // combustible o electricidad
  if (esElectrico) {
    // 0,18 kWh/km de referencia, tarifa comercial EEQ ~$0,10/kWh
    const kwh = km * 0.18 * uso;
    const costo = kwh * 0.10;
    filas.push(['Electricidad', (kwh.toFixed(0) + ' kWh × $0,10'), costo]);
  } else {
    // km/litro da LITROS; hay que convertir a galones (1 gal = 3,785 L)
    const litros = (km * uso) / kml;
    const galones = litros / 3.785;
    const costo = galones * pComb;
    filas.push(['Combustible',
      (litros.toFixed(0) + ' L = ' + galones.toFixed(1) + ' gal × ' + fmt(pComb)), costo]);
  }

  // matricula por cilindraje (rubros SRI/ANT prorrateados)
  let matriculaAnual;
  if (esElectrico) {
    matriculaAnual = 120;  // exoneración parcial por incentivos a eléctricos
  } else if (cc <= 1500) {
    matriculaAnual = 220;
  } else if (cc <= 2000) {
    matriculaAnual = 290;
  } else if (cc <= 2500) {
    matriculaAnual = 420;
  } else {
    matriculaAnual = 560;
  }
  filas.push(['Matrícula y rodaje', 'rubros SRI y ANT ÷ 12', matriculaAnual / 12]);

  // seguro
  const sppat = esElectrico ? 60 : (cc <= 1500 ? 95 : 135);
  let costoSe = sppat / 12;
  let descSeguro = 'SPPAT ÷ 12';
  if (pSeguro > 0) {
    costoSe = (precio * pSeguro) / 12 + sppat / 12;
    descSeguro = ((pSeguro * 100).toFixed(1) + '% del valor + SPPAT');
  }
  filas.push(['Seguro', descSeguro, costoSe]);

  // mantenimiento por km
  let mantAnual;
  if (esElectrico) {
    mantAnual = (km / 5000) * 45;   // sin aceite ni filtros
  } else {
    mantAnual = (km / 5000) * 120;
  }
  filas.push(['Mantenimiento', 'cada 5.000 km', mantAnual / 12]);

  // revision tecnica
  const rev = 45 * ciudad;
  filas.push(['Revisión técnica', 'según ciudad ÷ 12', rev / 12]);

  // totales
  const total = filas.reduce((a, f) => a + f[2], 0);
  const tbody = document.querySelector('#tabla tbody');
  tbody.innerHTML = filas.map(f =>
    '<tr><td>' + f[0] + '</td><td class="calc-desc">' + f[1] + '</td><td class="num">' + fmt(f[2]) + '</td></tr>'
  ).join('') + '<tr class="calc-sum"><td>Total</td><td></td><td class="num">' + fmt(total) + '</td></tr>';

  document.getElementById('total').textContent = fmt(total);
  document.getElementById('anual').textContent = fmt(total * 12);
  document.getElementById('porkm').textContent = '$' + (total / km).toFixed(3);

  // actualizar la URL con el estado para poder compartir el resultado
  const p = new URLSearchParams({
    m: sel.value, km: km, comb: pComb, ciu: document.getElementById('ciudad').value
  });
  history.replaceState(null, '', '?' + p.toString());
}

document.querySelectorAll('#calc select, #calc input').forEach(el => {
  el.addEventListener('change', calcular);
  el.addEventListener('input', calcular);
});

// restaurar estado desde la URL (enlaces compartibles)
const q = new URLSearchParams(location.search);
if (q.get('m')) sel.value = q.get('m');
if (q.get('km')) document.getElementById('km').value = q.get('km');
if (q.get('comb')) document.getElementById('precio_comb').value = q.get('comb');
if (q.get('ciu')) document.getElementById('ciudad').value = q.get('ciu');

calcular();
</script>"""

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
"""


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
        ],
    )
    (DIST / "calculadora.html").write_text(html, encoding="utf-8")
    print("  ✓ calculadora.html")


if __name__ == "__main__":
    main()
