"""OCR de fichas tecnicas que vienen como imagen (sin capa de texto).
Renderiza el PDF a PNG con pymupdf y lo pasa por RapidOCR.
"""
import sys
import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR

ruta = sys.argv[1] if len(sys.argv) > 1 else "fichas/kia_KiaSeltos.pdf"
salida = os.path.splitext(ruta)[0] + "_ocr.txt"

print(f"OCR de {ruta}")
doc = pymupdf.open(ruta)
print(f"  paginas: {len(doc)}")

ocr = RapidOCR()
todo = []

for n, pagina in enumerate(doc, 1):
    pix = pagina.get_pixmap(dpi=250)
    img = f"/tmp/_ocr_p{n}.png"
    pix.save(img)
    res, _ = ocr(img)
    lineas = [r[1] for r in res] if res else []
    print(f"  pagina {n}: {len(lineas)} lineas de texto detectadas")
    todo.append(f"===== PAGINA {n} =====")
    todo.extend(lineas)
    os.remove(img)

texto = "\n".join(todo)
open(salida, "w", encoding="utf-8").write(texto)
print(f"\n  escrito: {salida}  ({len(texto)} chars)\n")
print(texto)
