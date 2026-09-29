#!/usr/bin/env bash
# Kia publica fichas en un patron predecible. Probamos los modelos que faltan.
cd /opt/data/cuantocuesta-repo/fichas || exit 1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
BASE="https://www.kia.com/content/dam/kwcms/cl/es/files/fichas-tecnicas/FichasTecnicas"

for modelo in KiaSonet Sonet KiaSonet2025 KiaSoluto KiaSeltos KiaSportage; do
  for enc in "Ficha-T%C3%A9cnica-${modelo}" "Ficha-Tecnica-${modelo}"; do
    u="${BASE}/${enc}.pdf"
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -I -A "$UA" "$u" 2>/dev/null)
    if [ "$code" = "200" ]; then
      echo "  ENCONTRADO ($code): $u"
      curl -s -L --max-time 90 -A "$UA" -o "kia_${modelo}.pdf" "$u" 2>/dev/null
      echo "     bajado: $(wc -c < kia_${modelo}.pdf) bytes"
    fi
  done
done

echo
echo "════════ ¿que bajamos? ════════"
ls -la kia_*.pdf 2>/dev/null || echo "  ningun PDF de Kia"
