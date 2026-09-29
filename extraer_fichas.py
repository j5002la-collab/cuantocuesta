"""
Carga datos verificados de las fichas tecnicas a data/modelos.json
===================================================================

POR QUE ESTE DISENO Y NO UN PARSER AUTOMATICO
---------------------------------------------
Las fichas vienen de PDFs aplanados y cada marca usa una maqueta distinta:

  * Toyota pone el VALOR en la linea ANTERIOR a la etiqueta:
        2,694
        Cilindraje (cc)

  * Chery pone TODAS las etiquetas juntas y TODOS los valores despues:
        CAPACIDADES Y DIMENSIONES
        Longitud total
        Ancho total
        Alto total
        Distancia entre ejes
        114  HP @ 6150 RPM      <-- un parser ingenuo lo lee como "longitud"

Un parser automatico mete datos falsos. Esta tabla es MANUAL: cada dato
declara (archivo, ancla). El script exige que el ancla exista en el archivo
antes de escribir nada. Si un ancla no aparece, el dato se RECHAZA y se
reporta. No hay forma de que entre un numero inventado.

Para agregar un dato: verificalo leyendo la ficha y agrega la fila aqui.
"""

import json
import os
import re
import unicodedata
from collections import defaultdict

FICHAS = "fichas"
MODELOS = os.path.join("data", "modelos.json")

# (slug, campo, valor, archivo_fuente, ancla, nota)
# `ancla` es el texto que DEBE existir en el archivo para aceptar el dato.
DATOS = [
    # ---------------------------------------------------------------- CHERY ARRIZO 5
    # Fuente: Distrivehic (representante Chery en Ecuador), edicion 09/2022
    ("chery-arrizo", "potencia_hp", 114, "arrizo5_distrivehic_ec.txt",
     "114  HP @ 6150 RPM", "Version 1.5L MT, ficha Distrivehic EC"),
    ("chery-arrizo", "torque_nm", 141, "arrizo5_distrivehic_ec.txt",
     "141 Nm @ 3800 RPM", "Version 1.5L MT"),
    ("chery-arrizo", "cilindrada_cc", 1500, "arrizo5_distrivehic_ec.txt",
     "ACTECO DVVT", "Motor ACTECO 1.5L DVVT; cilindrada '1,500' en ficha"),
    ("chery-arrizo", "longitud", 4532, "arrizo5_distrivehic_ec.txt",
     "4.532 mm", "Longitud total"),
    ("chery-arrizo", "ancho", 1814, "arrizo5_distrivehic_ec.txt",
     "1.814 mm", "Ancho total"),
    ("chery-arrizo", "alto", 1487, "arrizo5_distrivehic_ec.txt",
     "1.487 mm", "Alto total"),
    ("chery-arrizo", "distancia_ejes", 2650, "arrizo5_distrivehic_ec.txt",
     "2.650 mm", "Distancia entre ejes"),
    ("chery-arrizo", "maletero_l", 430, "arrizo5_distrivehic_ec.txt",
     "430 L", "Volumen de maletero"),
    ("chery-arrizo", "airbags", 6, "arrizo5_distrivehic_ec.txt",
     "2 airbags conductor y pasajero", "2 delanteros + 2 laterales + 2 de cortina"),
    ("chery-arrizo", "transmision", "Manual 5 velocidades + reversa",
     "arrizo5_distrivehic_ec.txt", "5 velocidades + reversa", "Caja manual"),

    # ---------------------------------------------------------------- TOYOTA HILUX
    # Fuente: Toyota Ecuador (toyota.com.ec), versiones 4x2 CD Gasolina
    ("toyota-hilux", "potencia_hp", 163, "hilux_ec_toyota_oficial.txt",
     "163@5200", "4x2 CD Gasolina, motor 2TR-FE"),
    ("toyota-hilux", "torque_nm", 245, "hilux_ec_toyota_oficial.txt",
     "245@4000", "4x2 CD Gasolina"),
    ("toyota-hilux", "cilindrada_cc", 2694, "hilux_ec_toyota_oficial.txt",
     "2,694", "4x2 CD Gasolina"),
    ("toyota-hilux", "motor", "2.7 L 2TR-FE, 4 cil, DOHC Dual VVT-i",
     "hilux_ec_toyota_oficial.txt", "2TR-FE", "Motor a gasolina"),
    ("toyota-hilux", "simbolo_motor", "2TR-FE",
     "hilux_ec_toyota_oficial.txt", "2TR-FE", "Codigo de motor"),

    # ---------------------------------------------------------------- HYUNDAI TUCSON
    # Fuente: Hyundai Chile + Hyundai Ecuador (www.hyundai.com.ec)
    ("hyundai-tucson", "longitud", 4640, "tucson_hyundai_cl.txt",
     "4.640", "Version larga; la ficha EC muestra tambien 4.510"),
    ("hyundai-tucson", "ancho", 1865, "tucson_hyundai_cl.txt",
     "1.865", "Ancho total"),
    ("hyundai-tucson", "alto", 1665, "tucson_hyundai_cl.txt",
     "1.665", "Alto total"),
    ("hyundai-tucson", "distancia_ejes", 2755, "tucson_hyundai_cl.txt",
     "2.755", "Distancia entre ejes"),
    ("hyundai-tucson", "potencia_hp", 154, "tucson_hyundai_cl.txt",
     "154 Hp a 6,200 Rpm", "Motor 2.0 gasolina; el 1.6 turbo declara 178 hp"),
    ("hyundai-tucson", "torque_nm", 192, "tucson_hyundai_cl.txt",
     "192 Nm/4.500 Rpm", "Motor 2.0 gasolina; el 1.6 turbo declara 265 Nm"),
    ("hyundai-tucson", "maletero_l", 539, "tucson_hyundai_cl.txt",
     "539", "Volumen de maletero"),
    # ---------------------------------------------------------------- SUZUKI SWIFT
    # Fuente: ficha tecnica oficial Suzuki Ecuador (suzukiecuador.com), 2025-05
    ("suzuki-swift", "potencia_hp", 80, "swift_suzuki_ec.txt",
     "80 @ 5.700", "1.2L SHVS; el MGE aporta 3 HP adicionales"),
    ("suzuki-swift", "torque_nm", 112, "swift_suzuki_ec.txt",
     "112 @ 4.300", "1.2L SHVS; el MGE aporta 60 Nm adicionales"),
    ("suzuki-swift", "cilindrada_cc", 1197, "swift_suzuki_ec.txt",
     "1.2L + SHVS", "3 cilindros, 12 valvulas"),
    ("suzuki-swift", "longitud", 3860, "swift_suzuki_ec.txt",
     "3,860", "Largo total (mm)"),
    ("suzuki-swift", "ancho", 1735, "swift_suzuki_ec.txt",
     "1,735", "Ancho (mm)"),
    ("suzuki-swift", "alto", 1520, "swift_suzuki_ec.txt",
     "1,520", "Altura (mm)"),
    ("suzuki-swift", "distancia_ejes", 2450, "swift_suzuki_ec.txt",
     "2,450", "Distancia entre ejes (mm)"),
    ("suzuki-swift", "peso_kg", 928, "swift_suzuki_ec.txt",
     "928", "Peso en vacio (kg)"),
    ("suzuki-swift", "maletero_l", 265, "swift_suzuki_ec.txt",
     "265 L con asientos en posicion normal",
     "589 L con asientos plegados"),
    ("suzuki-swift", "transmision", "Manual 5 velocidades",
     "swift_suzuki_ec.txt", "5", "Traccion delantera (2WD)"),
    ("suzuki-swift", "airbags", 6, "swift_suzuki_ec.txt",
     "Airbags laterales x2", "2 frontales + 2 laterales + 2 de cortina"),
    ("suzuki-swift", "motor", "1.2L SHVS (Smart Hybrid by Suzuki), 3 cil",
     "swift_suzuki_ec.txt", "1.2L + SHVS", "Hibrido leve"),
]


def norm(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t)


def verificar(ancla, archivo, cache):
    """Devuelve True solo si el ancla aparece realmente en el archivo."""
    if archivo not in cache:
        ruta = os.path.join(FICHAS, archivo)
        if not os.path.exists(ruta):
            cache[archivo] = None
        else:
            cache[archivo] = norm(open(ruta, encoding="utf-8", errors="replace").read())
    contenido = cache[archivo]
    if contenido is None:
        return False, "archivo no encontrado"
    if norm(ancla) not in contenido:
        return False, "ancla no aparece en el archivo"
    return True, "ok"


def main():
    d = json.load(open(MODELOS, encoding="utf-8"))
    modelos = d["modelos"]
    por_slug = {m["slug"]: m for m in modelos}

    cache = {}
    aplicados = defaultdict(list)
    rechazados = []

    for slug, campo, valor, archivo, ancla, nota in DATOS:
        ok, motivo = verificar(ancla, archivo, cache)
        if not ok:
            rechazados.append((slug, campo, valor, archivo, ancla, motivo))
            continue
        m = por_slug.get(slug)
        if m is None:
            rechazados.append((slug, campo, valor, archivo, ancla, "modelo no existe en modelos.json"))
            continue
        m[campo] = valor
        aplicados[slug].append((campo, valor, archivo, nota))

    print("=" * 96)
    print("  DATOS APLICADOS (ancla verificada en la ficha)")
    print("=" * 96)
    for slug in sorted(aplicados):
        nombre = por_slug[slug]["nombre"]
        print(f"\n  {nombre}  ({slug})  -- {len(aplicados[slug])} campos")
        for campo, valor, archivo, nota in aplicados[slug]:
            print(f"     {campo:18} = {str(valor):38} [{archivo}]")
            print(f"       {nota}")

    if rechazados:
        print("\n" + "=" * 96)
        print("  RECHAZADOS (el ancla no existe -> NO se escribe el dato)")
        print("=" * 96)
        for slug, campo, valor, archivo, ancla, motivo in rechazados:
            print(f"     {slug}.{campo} = {valor}   [{archivo}]  -> {motivo}")
    else:
        print("\n  (ningun dato rechazado)")

    # actualizar meta
    d["meta"]["actualizado"] = "2026-09-29"
    fuentes = set(d["meta"].get("fuentes", []))
    fuentes.update([
        "Fichas tecnicas oficiales: Toyota Ecuador, Hyundai Ecuador/Chile, Chery (Distrivehic Ecuador)",
    ])
    d["meta"]["fuentes"] = sorted(fuentes)

    with open(MODELOS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"\n  modelos.json actualizado: {len(aplicados)} modelos tocados")

    # cobertura resultante
    print("\n" + "=" * 96)
    print("  COBERTURA POR MODELO (campos comparables cargados)")
    print("=" * 96)
    campos = ["precio_desde", "potencia_hp", "torque_nm", "consumo_mixto",
              "tanque_l", "maletero_l", "peso_kg", "airbags"]
    print("  modelo                  " + "  ".join(c[:9] for c in campos))
    for m in modelos:
        fila = "  ".join(("si" if m.get(c) else "NO").ljust(9) for c in campos)
        print(f"  {m['nombre'][:22]:23} {fila}")


if __name__ == "__main__":
    main()
