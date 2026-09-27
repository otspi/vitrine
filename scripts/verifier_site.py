#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Contrôle de cohérence des pages du site (non déployé).

Trois règles, vérifiées sur toutes les pages HTML :

- menu : chaque page porte le menu commun de sa langue (MENU ci-dessous), la page courante
  marquée par aria-current="page", un sélecteur de langue vers une page qui existe et
  l'appel à l'action (CTA, ci-dessous) ;
- versions : chaque feuille de style et script local est appelé avec ?v=<empreinte>, les huit
  premiers caractères du SHA-256 du fichier. Le CSS et le JavaScript étant mis en cache
  7 jours (.htaccess), l'empreinte change dès que le fichier change et force le rechargement ;
- partage : chaque page indexée (adresse canonique) déclare les balises Open Graph et Twitter,
  avec une image de assets/og/ qui existe et og:url égale à l'adresse canonique. Non corrigé
  automatiquement : titre, description et image se choisissent page par page.

Sans option, le script signale les écarts et sort avec le code 1 s'il en trouve.
Avec --corriger, il réécrit le menu et les versions en place.

    python3 scripts/verifier_site.py [--corriger]
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Menu commun : (cible, libellé). Une cible commençant par « / » désigne une page du site,
# « /#… » une section de l'accueil ; les autres sont des adresses externes.
MENU = {
    "fr": [
        ("/#pilote", "Démo"),
        ("https://about.otspi.org/livre-blanc/", "Livre blanc"),
        ("/manifeste.html", "Manifeste"),
        ("/faq.html", "FAQ"),
        ("/actualites.html", "Actualités"),
        ("/presse.html", "Presse"),
    ],
    "en": [
        ("/en/#pilot", "Demo"),
        ("https://about.otspi.org/white-paper/", "White paper"),
        ("/en/manifesto.html", "Manifesto"),
        ("/en/faq.html", "FAQ"),
        ("/en/news.html", "News"),
        ("/en/press.html", "Press"),
    ],
}
CTA = {"fr": ("/#partenaires", "Devenir partenaire"), "en": ("/en/#partners", "Become a partner")}
# Pages du manifeste : l'appel à l'action renvoie au formulaire de la page.
CTA_PAGE = {
    "manifeste.html": ("#signer", "Signer le manifeste"),
    "en/manifesto.html": ("#sign", "Sign the manifesto"),
}
# La page d'erreur est servie à n'importe quelle adresse : liens absolus.
ABSOLUE = {"404.html"}

NAV = re.compile(r'(<nav class="site-nav"[^>]*>\n)(\s*)<ul>\n.*?\n\s*</ul>', re.S)
LANG = re.compile(r'<li><a class="lang-switch"[^>]*></a></li>|<li><a class="lang-switch"[^\n]*</li>')
RESSOURCE = re.compile(r'(<(?:link|script)\b[^>]*?\b(?:href|src)=")([^"#?:]+\.(?:css|js))(?:\?v=[^"]*)?(")')


def pages():
    return sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("**/*.html")
                  if not any(part.startswith(".") or part == "scripts" for part in p.relative_to(ROOT).parts))


def relatif(cible, page):
    """Adresse de la cible vue depuis la page."""
    if not cible.startswith("/") or page in ABSOLUE:
        return cible
    chemin, _, ancre = cible.partition("#")
    dossier = page.rsplit("/", 1)[0] + "/" if "/" in page else ""
    if chemin.endswith("/"):
        chemin += "index.html"
    chemin = chemin.lstrip("/")
    if chemin == page:
        return "#" + ancre if ancre else chemin.rsplit("/", 1)[-1]
    if dossier and chemin.startswith(dossier):
        rel = chemin[len(dossier):]
    else:
        rel = "../" * page.count("/") + chemin
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")] or "./"
    return rel + ("#" + ancre if ancre else "")


def menu_attendu(page, indent, lang_switch):
    lang = "en" if page.startswith("en/") else "fr"
    lignes = [indent + "<ul>"]
    for cible, libelle in MENU[lang]:
        courant = ' aria-current="page"' if cible.lstrip("/") == page else ""
        lignes.append(f'{indent}  <li><a href="{relatif(cible, page)}"{courant}>{libelle}</a></li>')
    lignes.append(indent + "  " + lang_switch)
    cible, libelle = CTA_PAGE.get(page, CTA[lang])
    lignes.append(f'{indent}  <li><a class="nav-cta" href="{relatif(cible, page)}">{libelle}</a></li>')
    lignes.append(indent + "</ul>")
    return "\n".join(lignes)


def verifier_menu(page, texte, ecarts):
    m = NAV.search(texte)
    if not m:
        ecarts.append(f"{page} : menu de navigation absent")
        return texte
    lang_switch = LANG.search(m.group(0))
    if not lang_switch:
        ecarts.append(f"{page} : sélecteur de langue absent du menu")
        return texte
    lang_switch = lang_switch.group(0)
    href = re.search(r'href="([^"]+)"', lang_switch).group(1)
    cible = href.lstrip("/") if href.startswith("/") else (Path(page).parent / href).as_posix()
    cible = Path(ROOT / cible)
    if not (cible / "index.html" if href.endswith("/") else cible).resolve().is_file():
        ecarts.append(f"{page} : le sélecteur de langue pointe vers une page absente ({href})")
    attendu = m.group(1) + menu_attendu(page, m.group(2), lang_switch)
    if m.group(0) != attendu:
        ecarts.append(f"{page} : le menu diffère du menu commun")
        texte = texte[: m.start()] + attendu + texte[m.end():]
    return texte


PARTAGE = ("og:title", "og:description", "og:url", "og:image", "og:image:alt", "twitter:card", "twitter:image")


def verifier_partage(page, texte, ecarts):
    canonique = re.search(r'<link rel="canonical" href="([^"]+)">', texte)
    if not canonique:
        return
    balises = dict(re.findall(r'<meta (?:property|name)="((?:og|twitter):[\w:]+)" content="([^"]*)">', texte))
    manquantes = [b for b in PARTAGE if not balises.get(b)]
    if manquantes:
        ecarts.append(f"{page} : balises de partage absentes ({', '.join(manquantes)})")
        return
    if balises["og:url"] != canonique.group(1):
        ecarts.append(f"{page} : og:url ({balises['og:url']}) diffère de l'adresse canonique")
    for balise in ("og:image", "twitter:image"):
        chemin = balises[balise].removeprefix("https://www.otspi.org/")
        if chemin == balises[balise] or not (ROOT / chemin).is_file():
            ecarts.append(f"{page} : {balise} ne désigne pas une image du site ({balises[balise]})")


def verifier_versions(page, texte, ecarts, empreintes):
    def remplacer(m):
        chemin = m.group(2)
        fichier = (ROOT / chemin.lstrip("/")) if chemin.startswith("/") else (ROOT / page).parent / chemin
        fichier = fichier.resolve()
        if not fichier.is_file():
            ecarts.append(f"{page} : ressource absente ({chemin})")
            return m.group(0)
        if fichier not in empreintes:
            empreintes[fichier] = hashlib.sha256(fichier.read_bytes()).hexdigest()[:8]
        attendu = f"{m.group(1)}{chemin}?v={empreintes[fichier]}{m.group(3)}"
        if m.group(0) != attendu:
            ecarts.append(f"{page} : version à mettre à jour pour {chemin} (?v={empreintes[fichier]})")
        return attendu

    return RESSOURCE.sub(remplacer, texte)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--corriger", action="store_true", help="réécrire le menu et les versions en place")
    args = parser.parse_args()

    ecarts, empreintes, modifiees = [], {}, []
    for page in pages():
        fichier = ROOT / page
        texte = fichier.read_text(encoding="utf-8")
        verifier_partage(page, texte, ecarts)
        nouveau = verifier_versions(page, verifier_menu(page, texte, ecarts), ecarts, empreintes)
        if args.corriger and nouveau != texte:
            fichier.write_text(nouveau, encoding="utf-8")
            modifiees.append(page)

    for ecart in ecarts:
        print(ecart)
    if args.corriger:
        print(f"{len(modifiees)} page(s) corrigée(s)" + (" : " + ", ".join(modifiees) if modifiees else ""))
        return 0
    if ecarts:
        print(f"{len(ecarts)} écart(s). Menu et versions : python3 scripts/verifier_site.py --corriger ;"
              " balises de partage : à compléter à la main.")
        return 1
    print(f"{len(pages())} pages conformes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
