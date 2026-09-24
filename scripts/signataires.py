#!/usr/bin/env python3
"""Met à jour la liste publique des signataires du manifeste à partir d'un export CSV Framaforms.

Seules les personnes ayant consenti à la publication apparaissent dans la liste ;
les adresses e-mail ne sont jamais publiées. Les doublons (même e-mail) sont fusionnés
en conservant la réponse la plus récente.

Export attendu (Framaforms > Résultats > Télécharger) : format « Texte délimité »,
en-têtes de colonnes « Form Key », liste des options « Compact ».

Usage :
    python3 scripts/signataires.py export-framaforms.csv
    python3 scripts/signataires.py export.csv --exclure retraits.txt

L'export CSV et le fichier d'exclusions contiennent des données personnelles :
ils ne doivent jamais être ajoutés au dépôt.
"""

import argparse
import csv
import html
import re
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "manifeste.html"
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
    parser.add_argument("export", type=Path, help="export CSV des réponses Framaforms")
    parser.add_argument("--exclure", type=Path, help="fichier d'adresses e-mail à exclure (une par ligne)")
    for key, label in DEFAULT_COLUMNS.items():
        parser.add_argument(f"--col-{key}", default=label, help=f"libellé de la colonne (défaut : {label})")
    args = parser.parse_args()

    columns = {key: getattr(args, f"col_{key}") for key in DEFAULT_COLUMNS}
    rows = read_rows(args.export)
    header_index, positions = find_header(rows, columns)

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

    public = sorted(
        (s for s in signatures.values() if s["public"]),
        key=lambda s: (s["nom"].casefold(), s["prenom"].casefold()),
    )

    lines = [START]
    lines.append(
        f'        <p class="signatures-count"><strong>{len(signatures)}</strong> '
        f'signature{"s" if len(signatures) > 1 else ""}, dont {len(public)} publiée{"s" if len(public) > 1 else ""} '
        "avec l'accord de leurs auteurs.</p>"
    )
    if public:
        lines.append('        <ul class="signatures-list">')
        for s in public:
            quality = ", ".join(part for part in (s["fonction"], s["organisation"]) if part)
            full_name = " ".join(part for part in (s["prenom"], s["nom"]) if part)
            item = f"<strong>{html.escape(full_name)}</strong>"
            if quality:
                item += f'<span class="sig-quality">{html.escape(quality)}</span>'
            lines.append(f"          <li>{item}</li>")
        lines.append("        </ul>")
    lines.append(f"        {END}")

    page = PAGE.read_text(encoding="utf-8")
    start, end = page.find(START), page.find(END)
    if start == -1 or end == -1:
        sys.exit(f"Marqueurs SIGNATAIRES introuvables dans {PAGE.name}")
    page = page[:start] + "\n".join(lines) + page[end + len(END):]
    PAGE.write_text(page, encoding="utf-8")

    print(f"{len(signatures)} signature(s) valide(s), {len(public)} publiée(s) dans {PAGE.name}.")


if __name__ == "__main__":
    main()
