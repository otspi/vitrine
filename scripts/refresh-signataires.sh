#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Rafraîchit la liste publique des signataires à partir du dernier export CSV Framaforms.
#
# L'export (données personnelles) reste HORS du dépôt, dans ~/otspi-export/ :
#   ~/otspi-export/*.csv          exports Framaforms ; le plus récent est utilisé
#   ~/otspi-export/retraits.txt   facultatif : signatures retirées (une adresse e-mail par ligne)
#
# Si la liste change, le script committe uniquement manifeste.html et en/manifesto.html puis pousse.
# Le CSV n'est traité que s'il a changé depuis le dernier passage. Conçu pour être lancé par cron :
#   17 8 * * * /chemin/vers/otspi-vitrine/scripts/refresh-signataires.sh >> ~/otspi-export/refresh.log 2>&1

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="${OTSPI_EXPORT_DIR:-$HOME/otspi-export}"
STATE="$DIR/.dernier-export.sha256"
PAGES=(manifeste.html en/manifesto.html)

exec 9>"$DIR/.refresh.lock"
flock -n 9 || { echo "$(date -Is) déjà en cours"; exit 0; }

csv="$(ls -1t "$DIR"/*.csv 2>/dev/null | head -n1 || true)"
if [ -z "$csv" ]; then
  echo "$(date -Is) aucun export CSV dans $DIR"
  exit 0
fi

signature="$({ cat "$csv"; cat "$DIR/retraits.txt" 2>/dev/null || true; } | sha256sum | cut -d' ' -f1)"
if [ -f "$STATE" ] && [ "$(cat "$STATE")" = "$signature" ]; then
  echo "$(date -Is) export inchangé ($(basename "$csv"))"
  exit 0
fi

cd "$REPO"
if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
  echo "$(date -Is) dépôt hors de la branche main : abandon"
  exit 1
fi
if ! git diff --quiet -- "${PAGES[@]}" || ! git diff --cached --quiet; then
  echo "$(date -Is) modifications en cours dans le dépôt : abandon"
  exit 1
fi

git pull --quiet --rebase
args=("$csv")
[ -f "$DIR/retraits.txt" ] && args+=(--exclure "$DIR/retraits.txt")
python3 scripts/signataires.py "${args[@]}"

if git diff --quiet -- "${PAGES[@]}"; then
  echo "$(date -Is) liste inchangée"
else
  git add -- "${PAGES[@]}"
  git commit --quiet -m "chore: mise à jour de la liste des signataires"
  git push --quiet
  echo "$(date -Is) liste mise à jour et publiée"
fi
echo "$signature" > "$STATE"
