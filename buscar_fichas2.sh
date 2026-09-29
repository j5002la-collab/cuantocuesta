#!/usr/bin/env bash
# Busca las fichas tecnicas usando r.jina.ai (las webs cargan por JS).
cd /opt/data/cuantocuesta-repo/fichas || exit 1

probar() {
  local nombre="$1" url="$2"
  echo "════════ $nombre ════════"
  curl -s -L --max-time 50 "https://r.jina.ai/$url" 2>/dev/null \
    | grep -oiE "https?://[^ )\"']{0,150}(ficha|pdf|tecnica)[^ )\"']{0,60}" \
    | sort -u | head -6
  echo
}

probar "HYUNDAI GRAND i10" "https://www.hyundai.com.ec/vehiculos/grand-i10"
probar "HYUNDAI (home)" "https://www.hyundai.com.ec/"
probar "KIA SONET" "https://www.kia.com/ec/showroom/sonet/"
probar "GWM POER 500" "https://www.gwm-ecuador.ec/poer500"
probar "CHEVROLET D-MAX" "https://www.chevrolet.com.ec/camionetas/dmax"
