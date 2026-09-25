#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Vérifie les liens externes (http et https) présents dans des fichiers Markdown ou HTML.

Statuts :
  - cassé      : 404, 410, autre erreur 4xx / 5xx, erreur DNS ou de connexion, délai dépassé ;
  - à vérifier : 401, 403, 429, 999 — de nombreux sites refusent les requêtes automatisées ;
                 ces liens ne font pas échouer le contrôle mais sont listés.

Usage :
    python3 scripts/check_links.py docs                       # tous les .md et .html du dossier
    python3 scripts/check_links.py . --ignore scripts/links-ignore.txt
    python3 scripts/check_links.py docs --json /tmp/liens.json

Code de sortie : 0 si aucun lien cassé, 1 sinon. Aucune dépendance hors de la bibliothèque standard.
"""

import argparse
import concurrent.futures as cf
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = re.compile(r"https?://[^\s<>\"'\]\{\}`,;]+")
EXTENSIONS = {".md", ".html"}
SKIP_DIRS = {".git", "node_modules", "site", "__pycache__"}
SOFT = {401, 403, 429, 999}
LOCAL = ("localhost", "127.0.0.1", "0.0.0.0", "example.", ".example")
UA = "Mozilla/5.0 (compatible; OTSPI-link-check/1.0; +https://www.otspi.org)"


def collect(root, ignore):
    urls = {}
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.suffix not in EXTENSIONS or SKIP_DIRS & set(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in URL.finditer(text):
            url = match.group(0).rstrip(".:!?*_")
            # Les parenthèses font partie de certaines adresses ; on retire seulement celles en trop
            while url.endswith(")") and url.count("(") < url.count(")"):
                url = url[:-1].rstrip(".:!?*_")
            if any(token in url for token in LOCAL) or any(url.startswith(prefix) for prefix in ignore):
                continue
            urls.setdefault(url.split("#")[0], set()).add(str(path))
    return urls


def check(url):
    context = ssl.create_default_context()
    last = None
    for attempt in range(3):
        for method in ("HEAD", "GET"):
            try:
                request = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
                with urllib.request.urlopen(request, timeout=25, context=context) as response:
                    return url, response.status, None
            except urllib.error.HTTPError as error:
                last = error.code
                if method == "HEAD":
                    continue  # de nombreux serveurs répondent mal à HEAD : on confirme toujours en GET
                if error.code in SOFT or error.code in (404, 410):
                    return url, error.code, None
            except Exception as error:  # noqa: BLE001
                last = str(error)[:120]
        time.sleep(2 * (attempt + 1))
    return url, last if isinstance(last, int) else 0, None if isinstance(last, int) else last


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root")
    parser.add_argument("--ignore", help="fichier de préfixes d'URL à ignorer (un par ligne)")
    parser.add_argument("--json", help="écrit le résultat dans ce fichier")
    args = parser.parse_args()

    ignore = []
    if args.ignore and Path(args.ignore).is_file():
        ignore = [l.strip() for l in Path(args.ignore).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]

    urls = collect(args.root, ignore)
    broken, soft = [], []
    with cf.ThreadPoolExecutor(8) as pool:
        for url, status, error in pool.map(check, sorted(urls)):
            entry = {"url": url, "statut": status, "erreur": error, "fichiers": sorted(urls[url])}
            if status in SOFT:
                soft.append(entry)
            elif not (status and 200 <= status < 400):
                broken.append(entry)

    print(f"{len(urls)} liens uniques : {len(broken)} cassés, {len(soft)} à vérifier manuellement")
    for entry in broken:
        print(f"  CASSÉ  {entry['statut'] or entry['erreur']}  {entry['url']}  ({', '.join(entry['fichiers'][:2])})")
    for entry in soft:
        print(f"  À VÉRIFIER  {entry['statut']}  {entry['url']}")
    if args.json:
        Path(args.json).write_text(json.dumps({"total": len(urls), "casses": broken, "a_verifier": soft}, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
