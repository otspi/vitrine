#!/usr/bin/env bash
# SPDX-License-Identifier: EUPL-1.2
# Rafraîchit la liste publique des signataires à partir de l'application de signature
# (https://manifesto-sign.otspi.org/signataires.php) et, s'il y en a, d'un export CSV Framaforms
# historique.
#
# Données locales, HORS du dépôt, dans ~/otspi-export/ :
#   ~/otspi-export/*.csv          facultatif : exports Framaforms ; le plus récent est utilisé
#   ~/otspi-export/retraits.txt   facultatif : adresses à exclure des exports CSV (une par ligne)
#
# Si la liste change, le script committe uniquement manifeste.html et en/manifesto.html puis pousse.
# Aucun traitement si ni la liste JSON ni les fichiers locaux n'ont changé depuis le dernier passage.
# Conçu pour être lancé par cron :
#   17 8 * * * /chemin/vers/otspi-vitrine/scripts/refresh-signataires.sh >> ~/otspi-export/refresh.log 2>&1
# Variable facultative : SIGN_URL (adresse de la liste JSON).

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="${OTSPI_EXPORT_DIR:-$HOME/otspi-export}"
SIGN_URL="${SIGN_URL:-https://manifesto-sign.otspi.org/signataires.php}"
STATE="$DIR/.dernier-export.sha256"
PAGES=(manifeste.html en/manifesto.html)

exec 9>"$DIR/.refresh.lock"
flock -n 9 || { echo "$(date -Is) déjà en cours"; exit 0; }

feed="$(mktemp)"
trap 'rm -f "$feed"' EXIT
if ! curl -fsS -m 30 -o "$feed" "$SIGN_URL"; then
  echo "$(date -Is) liste JSON inaccessible ($SIGN_URL) : abandon, rien n'est modifié"
  exit 1
fi
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert isinstance(d.get("signataires"), list) and "total" in d' "$feed" \
  || { echo "$(date -Is) réponse JSON invalide : abandon"; exit 1; }

csv="$(ls -1t "$DIR"/*.csv 2>/dev/null | head -n1 || true)"
signature="$({ cat "$feed"; [ -n "$csv" ] && cat "$csv"; cat "$DIR/retraits.txt" 2>/dev/null || true; } | sha256sum | cut -d' ' -f1)"
if [ -f "$STATE" ] && [ "$(cat "$STATE")" = "$signature" ]; then
  echo "$(date -Is) sources inchangées"
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
args=(--json "$feed")
[ -n "$csv" ] && args+=("$csv")
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
