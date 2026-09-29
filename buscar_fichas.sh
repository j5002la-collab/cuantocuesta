#!/usr/bin/env bash
# Busca fichas tecnicas (PDF) en las webs de marca de Ecuador.
cd /opt/data/cuantocuesta-repo/fichas || exit 1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

buscar_pdf() {
  local nombre="$1" url="$2"
  echo "════════ $nombre ════════"
  echo "  $url"
  curl -s -L --max-time 35 -A "$UA" "$url" 2>/dev/null \
    | grep -oiE 'href="[^"]{0,160}\.pdf"' \
    | sort -u | head -8
  echo
}

buscar_pdf "GWM POER 500" "https://www.gwm-ecuador.ec/poer500"
buscar_pdf "GWM POER MT" "https://www.gwm-ecuador.ec/poermt"
buscar_pdf "CHEVROLET D-MAX" "https://www.chevrolet.com.ec/camionetas/dmax"
buscar_pdf "KIA SONET" "https://www.kia.com/ec/showroom/sonet/"
buscar_pdf "HYUNDAI GRAND i10" "https://www.hyundai.com.ec/vehiculos/grand-i10"

echo "════════ HYUNDAI via proxy r.jina.ai ════════"
curl -s -L --max-time 45 "https://r.jina.ai/https://www.hyundai.com.ec" 2>/dev/null \
  | grep -oiE "https?://[^ )\"']{0,140}\.pdf" | sort -u | head -10
