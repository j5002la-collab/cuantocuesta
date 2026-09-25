#!/usr/bin/env python3
"""
Sistema de anuncios de AdSense para cuantocuesta.xyz.

Se activa solo cuando data/ads.json tiene el publisher_id relleno.
Hasta entonces el sitio se construye igual, sin anuncios y sin errores:
asi el codigo queda listo y la activacion es cambiar un valor.

Genera ademas el ads.txt (requisito de Google Publisher Policies).
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
ASSETS = BASE / "assets"

_CFG = None


def config():
    global _CFG
    if _CFG is None:
        try:
            _CFG = json.loads((DATA / "ads.json").read_text(encoding="utf-8"))
        except Exception:
            _CFG = {"publisher_id": "", "slots": {}}
    return _CFG


def pub_id():
    """Devuelve el publisher ID normalizado (ca-pub-XXXX) o '' si no hay."""
    p = (config().get("publisher_id") or "").strip()
    if not p:
        return ""
    if not p.startswith("ca-"):
        p = "ca-" + p
    return p


def activo():
    """El script del <head> se inserta siempre que haya publisher ID."""
    return bool(pub_id())


def modo():
    return (config().get("modo") or "verificacion").strip().lower()


def mostrar_bloques():
    """Los bloques solo van cuando la cuenta esta aprobada.

    Antes de la aprobacion se quedan como huecos vacios y afean el sitio.
    """
    return activo() and modo() == "activo"


def bloque(nombre):
    """HTML de un bloque de anuncio. Cadena vacia si no corresponde mostrarlo."""
    if not mostrar_bloques():
        return ""
    p = pub_id()
    s = (config().get("slots") or {}).get(nombre) or {}
    if not s.get("activo"):
        return ""
    cliente = p.replace("ca-", "")
    fmt = s.get("formato", "auto")
    extra = ""
    if s.get("layout"):
        extra = f' data-ad-layout="{s["layout"]}"'
    return (
        '<div class="anuncio" data-slot="' + nombre + '">'
        '<span class="anuncio-etiq">Publicidad</span>'
        f'<ins class="adsbygoogle" style="display:block" '
        f'data-ad-client="{cliente}" data-ad-slot="{s.get("slot_id", "auto")}" '
        f'data-ad-format="{fmt}"{extra} data-full-width-responsive="true"></ins>'
        '<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>'
        '</div>'
    )


def encabezado():
    """Script de AdSense para el <head>. Vacio si no esta configurado."""
    p = pub_id()
    if not p:
        return ""
    return ('<script async src="https://pagead2.googlesyndication.com/'
            f'pagead/js/adsbygoogle.js?client={p}" crossorigin="anonymous"></script>')


def insertar_en_cuerpo(cuerpo_html):
    """Inserta los bloques respetando el flujo: tras el 1er parrafo y tras el 2do h2.

    Nunca al principio (antes del titulo) ni pegado a otro bloque.
    """
    if not activo():
        return cuerpo_html

    bloques = []
    # 1er parrafo: el de mejor rendimiento, el lector ya empezo
    b1 = bloque("cabecera")
    if b1:
        m = re.search(r"</p>", cuerpo_html)
        if m:
            i = m.end()
            cuerpo_html = cuerpo_html[:i] + "\n" + b1 + "\n" + cuerpo_html[i:]
            bloques.append("cabecera")

    # tras el 2do h2
    b2 = bloque("cuerpo")
    if b2:
        h2s = list(re.finditer(r"</h2>", cuerpo_html))
        if len(h2s) >= 2:
            i = h2s[1].end()
            cuerpo_html = cuerpo_html[:i] + "\n" + b2 + "\n" + cuerpo_html[i:]
            bloques.append("cuerpo")

    return cuerpo_html


def bloque_final():
    """Bloque al cerrar el articulo."""
    return bloque("final")


def generar_ads_txt():
    """Escribe assets/static/ads.txt si hay publisher ID. Devuelve True si lo hizo."""
    p = pub_id()
    if not p:
        return False
    linea = f"google.com, {p.replace('ca-', '')}, DIRECT, f08c47fec0942fa0\n"
    destino = ASSETS / "static"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "ads.txt").write_text(
        linea + "\n# cuantocuesta.xyz - vendedor autorizado de su propio inventario\n",
        encoding="utf-8")
    return True


CSS_ANUNCIO = """
.anuncio{margin:26px 0;padding:14px;background:var(--card);border:1px solid var(--bd);
  border-radius:10px;text-align:center;min-height:110px}
.anuncio-etiq{display:block;color:var(--mut);font-size:.68rem;text-transform:uppercase;
  letter-spacing:.09em;margin-bottom:9px}
.anuncio ins{background:transparent}
@media(max-width:600px){.anuncio{margin:20px 0;min-height:100px}}
"""


if __name__ == "__main__":
    p = pub_id()
    print(f"AdSense activo: {'SI (' + p + ')' if p else 'NO — falta publisher_id en data/ads.json'}")
    if p:
        print(f"ads.txt generado: {generar_ads_txt()}")
    else:
        print("\nPara activar: pon el publisher_id en data/ads.json y reconstruye.")
        print("El sitio no cambia hasta entonces (no hay anuncios ni huecos vacios).")
