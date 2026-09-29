#!/usr/bin/env bash
# Kia tiene un archivo mal etiquetado. Probamos la otra variante de nombre.
cd /opt/data/cuantocuesta-repo/fichas || exit 1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
BASE="https://www.kia.com/content/dam/kwcms/cl/es/files/fichas-tecnicas/FichasTecnicas"

echo "════════ bajando Ficha-Tecnica-Seltos.pdf ════════"
curl -s -L --max-time 120 -A "$UA" -o seltos_alt.pdf "${BASE}/Ficha-T%C3%A9cnica-Seltos.pdf" 2>/dev/null
echo "  bytes: $(wc -c < seltos_alt.pdf)"

echo
echo "════════ ¿tiene capa de texto? ════════"
cd /opt/data/cuantocuesta-repo
/opt/data/.venv/bin/python -c "
import pymupdf
d = pymupdf.open('fichas/seltos_alt.pdf')
t = ''.join(p.get_text() for p in d)
print(f'  paginas: {len(d)}  texto: {len(t)} chars')
if len(t) > 100:
    open('fichas/seltos_cl.txt','w',encoding='utf-8').write(t)
    print('  -> tiene texto, guardado como seltos_cl.txt')
    head = [l.strip() for l in t.splitlines() if l.strip()][:12]
    for l in head: print('    ', l[:90])
else:
    print('  -> es imagen, hay que OCR')
"