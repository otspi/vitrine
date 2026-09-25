#!/usr/bin/env python3
"""Met à jour la liste publique des signataires du manifeste à partir d'un export CSV Framaforms.

Seules les personnes ayant consenti à la publication apparaissent dans la liste ;
les adresses e-mail ne sont jamais publiées. Les doublons (même e-mail) sont fusionnés
en conservant la réponse la plus récente.

Export attendu (Framaforms > Résultats > Télécharger) : format « Texte délimité »,
en-têtes de colonnes « Form Key », liste des options « Compact ».

Les signataires de base (scripts/signataires-base.json), qui ont consenti à figurer
dans la liste, sont toujours ajoutés aux signatures issues du formulaire.

Usage :
    python3 scripts/signataires.py                     # signataires de base uniquement
    python3 scripts/signataires.py export-framaforms.csv
    python3 scripts/signataires.py export.csv --exclure retraits.txt

L'export CSV et le fichier d'exclusions contiennent des données personnelles :
ils ne doivent jamais être ajoutés au dépôt.
"""

import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_SIGNATORIES = Path(__file__).resolve().parent / "signataires-base.json"
# Pages mises à jour et libellés du compteur, par langue
PAGES = {
    ROOT / "manifeste.html": "fr",
    ROOT / "en" / "manifesto.html": "en",
}
START = "<!-- SIGNATAIRES:DEBUT — contenu généré par scripts/signataires.py, ne pas modifier à la main -->"
END = "<!-- SIGNATAIRES:FIN -->"

# Clés (Form Key) des champs du formulaire Framaforms (voir README)
DEFAULT_COLUMNS = {
    "prenom": "prenom",
    "nom": "nom",
    "email": "adresse_e_mail",
    "fonction": "fonction",
    "organisation": "organisation",
    "publication": "publication",
}


def normalize(label):
    return re.sub(r"\s+", " ", label).strip().casefold()


def read_rows(path):
    """Lit l'export en détectant le séparateur et la ligne d'en-tête."""
    text = path.read_text(encoding="utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return list(csv.reader(text.splitlines(), dialect))


def find_header(rows, columns):
    wanted = {normalize(label) for label in columns.values()}
    for index, row in enumerate(rows[:10]):
        cells = {normalize(cell) for cell in row}
        if {normalize(columns[key]) for key in ("prenom", "nom", "email")} <= cells:
            missing = wanted - cells
            if missing:
                sys.exit(f"Colonnes introuvables dans l'export : {', '.join(sorted(missing))}")
            return index, {normalize(cell): i for i, cell in enumerate(row)}
    sys.exit("Ligne d'en-tête introuvable : vérifier les libellés des colonnes (--col-*).")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("export", type=Path, nargs="?", help="export CSV des réponses Framaforms (facultatif)")
    parser.add_argument("--exclure", type=Path, help="fichier d'adresses e-mail à exclure (une par ligne)")
    for key, label in DEFAULT_COLUMNS.items():
        parser.add_argument(f"--col-{key}", default=label, help=f"libellé de la colonne (défaut : {label})")
    args = parser.parse_args()

    columns = {key: getattr(args, f"col_{key}") for key in DEFAULT_COLUMNS}
    if args.export:
        rows = read_rows(args.export)
        header_index, positions = find_header(rows, columns)
    else:
        rows, header_index, positions = [], -1, {}

    def cell(row, key):
        position = positions[normalize(columns[key])]
        return row[position].strip() if position < len(row) else ""

    excluded = set()
    if args.exclure:
        excluded = {line.strip().casefold() for line in args.exclure.read_text(encoding="utf-8").splitlines() if line.strip()}

    # Les exports sont chronologiques : la dernière réponse d'une même adresse l'emporte
    signatures = {}
    for row in rows[header_index + 1:]:
        if not any(row):
            continue
        email = cell(row, "email").casefold()
        first_name, last_name = cell(row, "prenom"), cell(row, "nom")
        if not email or not last_name or email in excluded:
            continue
        signatures[email] = {
            "prenom": first_name,
            "nom": last_name,
            "fonction": cell(row, "fonction"),
            "organisation": cell(row, "organisation"),
            "public": bool(cell(row, "publication")),
        }

    # Signataires de base : clé propre, pour ne pas dépendre d'une adresse e-mail
    if BASE_SIGNATORIES.is_file():
        for entry in json.loads(BASE_SIGNATORIES.read_text(encoding="utf-8")):
            key = "base:" + normalize(f"{entry['prenom']} {entry['nom']}")
            duplicates = [email for email, s in signatures.items()
                          if normalize(f"{s['prenom']} {s['nom']}") == key[5:]]
            for email in duplicates:
                del signatures[email]
            signatures[key] = {
                "prenom": entry["prenom"],
                "nom": entry["nom"],
                "fonction": entry.get("fonction", ""),
                "fonction_en": entry.get("fonction_en", ""),
                "organisation": entry.get("organisation", ""),
                "public": True,
            }

    public = sorted(
        (s for s in signatures.values() if s["public"]),
        key=lambda s: (s["nom"].casefold(), s["prenom"].casefold()),
    )

    def render(lang):
        total, shown = len(signatures), len(public)
        if lang == "en":
            head = f'<strong>{total}</strong> signature{"s" if total != 1 else ""}'
            if shown == total:
                tail = "published with the author's consent." if total == 1 else "all published with their authors' consent."
            else:
                tail = f"{shown} of which {'are' if shown != 1 else 'is'} published with their authors' consent."
        else:
            head = f'<strong>{total}</strong> signature{"s" if total > 1 else ""}'
            if shown == total:
                tail = "publiée avec l'accord de son auteur." if total == 1 else "toutes publiées avec l'accord de leurs auteurs."
            else:
                tail = f"dont {shown} publiée{'s' if shown > 1 else ''} avec l'accord de leurs auteurs."
        count = f"{head}, {tail}"
        lines = [START, f'        <p class="signatures-count">{count}</p>']
        if public:
            lines.append('        <ul class="signatures-list">')
            for s in public:
                role = s.get("fonction_en") if lang == "en" and s.get("fonction_en") else s["fonction"]
                quality = ", ".join(part for part in (role, s["organisation"]) if part)
                full_name = " ".join(part for part in (s["prenom"], s["nom"]) if part)
                item = f"<strong>{html.escape(full_name)}</strong>"
                if quality:
                    item += f'<span class="sig-quality">{html.escape(quality)}</span>'
                lines.append(f"          <li>{item}</li>")
            lines.append("        </ul>")
        lines.append(f"        {END}")
        return "\n".join(lines)

    for page_path, lang in PAGES.items():
        page = page_path.read_text(encoding="utf-8")
        start, end = page.find(START), page.find(END)
        if start == -1 or end == -1:
            sys.exit(f"Marqueurs SIGNATAIRES introuvables dans {page_path.name}")
        page_path.write_text(page[:start] + render(lang) + page[end + len(END):], encoding="utf-8")

    print(f"{len(signatures)} signature(s) valide(s), {len(public)} publiée(s) dans {', '.join(p.name for p in PAGES)}.")


if __name__ == "__main__":
    main()
