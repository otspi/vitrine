#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Met à jour les dates <lastmod> de sitemap.xml d'après Git (lancé au déploiement, non déployé).

Chaque adresse prend la date de la dernière arrivée sur main de sa page (git log --first-parent),
comme les dates de fichiers du déploiement. Le fichier sitemap.xml prend lui-même la date de la
page la plus récente : lftp ne le renvoie que si une page a changé.

    python3 scripts/sitemap_lastmod.py
"""
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
SITE = "https://www.otspi.org/"
URL = re.compile(r"(<loc>([^<]+)</loc>\s*<lastmod>)([^<]*)(</lastmod>)")


def date_git(chemin):
    sortie = subprocess.run(["git", "log", "-1", "--first-parent", "--format=%ct", "--", chemin],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if not sortie:
        raise SystemExit(f"{chemin} : aucun commit, page absente du dépôt ?")
    return int(sortie)


def page(adresse):
    if not adresse.startswith(SITE):
        raise SystemExit(f"Adresse hors du site : {adresse}")
    chemin = adresse[len(SITE):]
    return chemin + "index.html" if chemin == "" or chemin.endswith("/") else chemin


def main():
    texte = SITEMAP.read_text(encoding="utf-8")
    dates = []

    def remplacer(m):
        instant = date_git(page(m.group(2)))
        dates.append(instant)
        jour = datetime.fromtimestamp(instant, timezone.utc).strftime("%Y-%m-%d")
        return f"{m.group(1)}{jour}{m.group(4)}"

    nouveau = URL.sub(remplacer, texte)
    if not dates:
        raise SystemExit("Aucune entrée <lastmod> trouvée dans sitemap.xml")
    SITEMAP.write_text(nouveau, encoding="utf-8")
    os.utime(SITEMAP, (max(dates), max(dates)))
    print(f"sitemap.xml : {len(dates)} dates mises à jour")


if __name__ == "__main__":
    main()
