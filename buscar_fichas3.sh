#!/usr/bin/env bash
# Ultimos intentos para las fichas que faltan.
cd /opt/data/cuantocuesta-repo/fichas || exit 1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

echo "════════ KIA: pagina de descarga de catalogo ════════"
curl -s -L --max-time 35 -A "$UA" "https://www.kia.com/ec/shopping-tools/download-a-brochure.html" 2>/dev/null \
  | grep -oiE 'href="[^"]{0,170}\.pdf"|/content/dam/[^"]{0,140}\.pdf' | sort -u | head -10
echo

echo "════════ CHEVROLET D-MAX via r.jina.ai ════════"
curl -s -L --max-time 45 "https://r.jina.ai/https://www.chevrolet.com.ec/camionetas/dmax" 2>/dev/null \
  | grep -oiE "https?://[^ )\"']{0,150}\.pdf|ficha[^ .]{0,40}" | sort -u | head -10
echo

echo "════════ HYUNDAI: probando patron de ficha ════════"
for modelo in grand-i10-i10 i10 grand-i10 nuevo-grand-i10; do
  for u in "https://www.hyundai.com.ec/static/media/${modelo}-ficha-tecnica.pdf" \
           "https://www.hyundai.com.ec/static/media/ficha-tecnica-${modelo}.pdf"; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 12 -I -A "$UA" "$u" 2>/dev/null)
    [ "$code" = "200" ] && echo "  ENCONTRADO ($code): $u"
  done
done
echo "  (si no imprimio nada, el patron no matchea: los archivos llevan hash)"
echo

echo "════════ KIA SONET: ficha directa por patron ════════"
for u in "https://www.kia.com/content/dam/kwcms/ec/es/pdf/ficha-tecnica-sonet.pdf" \
         "https://www.kia.com/ec/showroom/sonet/ficha-tecnica.html"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -L -A "$UA" "$u" 2>/dev/null)
  echo "  $code  $u"
done
