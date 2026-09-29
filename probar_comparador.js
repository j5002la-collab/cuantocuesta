// Prueba funcional del comparador: simula el DOM y ejecuta el JS real
// que va embebido en dist/comparador.html.
const fs = require("fs");

const html = fs.readFileSync("/opt/data/cuantocuesta-repo/dist/comparador.html", "utf8");
const i = html.lastIndexOf("<script>");
const j = html.lastIndexOf("</script>");
const js = html.slice(i + 8, j);

// --- DOM simulado ---
const elementos = {};
function crearEl(id) {
  return {
    id, value: id === "cmp-a" ? "kia-soluto" : "chevrolet-groove",
    innerHTML: "",
    addEventListener: function () {},
  };
}
elementos["cmp-a"] = crearEl("cmp-a");
elementos["cmp-b"] = crearEl("cmp-b");
elementos["cmp-tabla"] = { innerHTML: "", innerHTMLset: true };
elementos["cmp-veredicto"] = { innerHTML: "" };

global.document = {
  readyState: "complete",
  getElementById: (id) => elementos[id] || null,
  addEventListener: () => {},
};
global.window = { history: { replaceState: () => {} }, location: { search: "" } };
global.URLSearchParams = class { constructor() {} get() { return null; } };

// ejecutar el JS real del sitio
try {
  eval(js);
} catch (e) {
  console.log("  ✗ el JS fallo:", e.message);
  process.exit(1);
}

const tabla = elementos["cmp-tabla"].innerHTML;
const veredicto = elementos["cmp-veredicto"].innerHTML;

console.log("  ✓ el JS corrio sin errores\n");
console.log("  --- VEREDICTO ---");
console.log("  " + veredicto.replace(/<[^>]+>/g, "").trim().slice(0, 160));

const filas = (tabla.match(/<tr><th>/g) || []).length;
const grupos = (tabla.match(/cmp-grupo/g) || []).length;
const mejores = (tabla.match(/cmp-mejor/g) || []).length;
const vacios = (tabla.match(/No publicado/g) || []).length;

console.log("\n  --- TABLA ---");
console.log(`  filas de datos:   ${filas}`);
console.log(`  grupos:           ${grupos}`);
console.log(`  celdas ganadoras: ${mejores}`);
console.log(`  celdas sin dato:  ${vacios}`);
console.log(`  largo del HTML:   ${tabla.length} chars`);

// mostrar las primeras filas como texto
const texto = tabla
  .replace(/<\/tr>/g, "\n")
  .replace(/<\/t[dh]>/g, " | ")
  .replace(/<[^>]+>/g, "")
  .split("\n")
  .map((l) => l.replace(/\s+/g, " ").trim())
  .filter((l) => l);

console.log("\n  --- PRIMERAS FILAS ---");
texto.slice(0, 8).forEach((l) => console.log("  " + l.slice(0, 95)));

const ok = filas > 0 && mejores > 0 && veredicto.length > 20;
console.log(`\n  ${ok ? "✓ COMPARADOR FUNCIONA" : "✗ ALGO FALLA"}`);
process.exit(ok ? 0 : 1);
