"""
Buscador de candidatos en las fichas tecnicas.
NO escribe nada: solo muestra cada coincidencia con su contexto
para poder VERIFICAR a mano antes de cargar un dato en modelos.json.
"""
import os
import re
import unicodedata

FICHAS = "fichas"

# etiquetas que buscamos, con variantes reales que aparecen en las fichas
ETIQUETAS = {
    "potencia_hp":   [r"potencia\s*(m[aá]xima)?", r"potencia\s*\(hp", r"\bhp\b"],
    "torque_nm":     [r"torque"],
    "cilindrada":    [r"cilindra(je|da)", r"cilindrada\s*\(cc\)", r"\bcc\b"],
    "longitud":      [r"longitud"],
    "ancho":         [r"ancho"],
    "alto":          [r"alto\s*total", r"altura"],
    "distancia_ejes":[r"distancia\s*entre\s*ejes", r"entre\s*ejes"],
    "peso_kg":       [r"peso", r"masa"],
    "tanque_l":      [r"tanque", r"capacidad\s*de\s*combustible", r"combustible\s*\("],
    "maletero_l":    [r"maletero", r"ba[uú]l", r"capacidad\s*del\s*ba[uú]l", r"volumen\s*de\s*equipaje"],
    "airbags":       [r"airbag"],
    "consumo":       [r"consumo", r"rendimiento", r"km/l", r"km\s*/\s*l"],
    "transmision":   [r"transmisi[oó]n"],
}

def limpio(t):
    """Normaliza acentos y colapsa espacios para poder buscar."""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[ \t]+", " ", t)

def contexto(lineas, i, antes=2, despues=3):
    a = max(0, i - antes)
    d = min(len(lineas), i + despues + 1)
    return " | ".join(l.strip() for l in lineas[a:d] if l.strip())

def main():
    archivos = sorted(f for f in os.listdir(FICHAS)
                      if f.endswith(".txt") and f != "urls.txt")
    print(f"fichas: {len(archivos)}\n")
    print("=" * 100)

    for arch in archivos:
        ruta = os.path.join(FICHAS, arch)
        try:
            raw = open(ruta, encoding="utf-8", errors="replace").read()
        except Exception as e:
            print(f"{arch}: ERROR {e}")
            continue

        lineas = raw.splitlines()
        norm = [limpio(l).lower() for l in lineas]

        encontrados = {}
        for campo, pats in ETIQUETAS.items():
            hits = []
            for i, l in enumerate(norm):
                for p in pats:
                    if re.search(p, l):
                        hits.append((i, contexto(lineas, i)))
                        break
                if len(hits) >= 4:
                    break
            if hits:
                encontrados[campo] = hits

        print(f"\n### {arch}   ({len(raw)} chars, {len(lineas)} lineas)")
        if not encontrados:
            print("    sin coincidencias")
            continue
        for campo, hits in encontrados.items():
            print(f"  [{campo}]")
            for i, ctx in hits[:3]:
                print(f"     L{i}: {ctx[:190]}")

if __name__ == "__main__":
    main()
