#!/usr/bin/env bash
echo "════════ ¿se puede instalar tesseract? ════════"
command -v apt-get >/dev/null 2>&1 && echo "  apt-get presente" || echo "  apt-get NO"
command -v apk >/dev/null 2>&1 && echo "  apk presente (alpine)" || echo "  apk NO"
id -u
[ "$(id -u)" = "0" ] && echo "  somos root" || echo "  NO somos root"
echo

echo "════════ ¿uv puede instalar OCR en python? ════════"
command -v uv >/dev/null 2>&1 && echo "  uv presente" || echo "  uv NO"
echo

echo "════════ KIA ECUADOR: precio del Seltos ════════"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
for u in "https://www.kia.com/ec/showroom/seltos/" "https://www.kia.com/ec/showroom/seltos/precio.html"; do
  echo "  --- $u"
  curl -s -L --max-time 30 -A "$UA" "$u" 2>/dev/null \
    | grep -oiE '\$[0-9]{2}[.,][0-9]{3}|USD [0-9]{2}[.,][0-9]{3}|[0-9]{2}[.,][0-9]{3} USD' \
    | sort -u | head -8
done
