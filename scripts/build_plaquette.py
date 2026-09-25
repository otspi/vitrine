#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Génère la plaquette d'une page (A4) d'OTSPI, en français et en anglais, au format PDF.

Les PDF sont écrits dans assets/docs/. L'impression est faite par Chrome ou Chromium en mode
headless ; la variable d'environnement CHROME permet d'imposer le binaire.

Usage :
    python3 scripts/build_plaquette.py

Tous les chiffres de la plaquette sont ceux de la page d'accueil du site et du livre blanc ;
les mettre à jour ensemble.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent / "plaquette"
OUT = ROOT / "assets" / "docs"
LOGO = ROOT / "assets" / "logo-horizontal-transparent-dark.svg"

TEXTS = {
    "fr": {
        "lang": "fr",
        "title": "OTSPI — Plaquette de présentation",
        "kicker": "Livre blanc · consultation publique v0.9",
        "h1": "Les services de confiance eIDAS comme commun numérique européen",
        "lead": "OTSPI est une initiative d'intérêt général, en cours de constitution sous forme d'association loi&nbsp;1901. Elle construit un prestataire de services de confiance ouvert, auditable et inaliénable : horodatage, certificats, cachet, signature et identité, par API normalisées et sans tarification à l'acte.",
        "figures_h": "Pourquoi maintenant",
        "figures": [
            ("24.12.2026", "date limite de mise à disposition du portefeuille européen d'identité numérique dans chaque État membre"),
            ("10 millions", "d'acteurs économiques concernés par la facturation électronique obligatoire en France (périmètre le plus large)"),
            ("≈ 10 000 €", "HT par an pour horodater 15&nbsp;000 documents par mois, au tarif public d'un prestataire qualifié"),
            ("47 jours", "de validité maximale d'un certificat Web en 2029, contre 398 en 2025 : l'automatisation devient obligatoire"),
        ],
        "problem_h": "Le constat",
        "problem": [
            "<strong>280 prestataires qualifiés</strong> dans l'EEE, mais un même modèle : contrat préalable, tarification à l'unité, interfaces propriétaires, marchés cloisonnés par pays.",
            "Les <strong>PME, collectivités, universités et projets open source</strong> sont exclus de fait de la preuve qualifiée.",
            "<strong>64 %</strong> des sites Web reposent sur une seule autorité de certification, établie hors de l'Union.",
        ],
        "answer_h": "Notre réponse",
        "answer": [
            "<strong>Code entièrement ouvert</strong> (EUPL&nbsp;1.2), API normalisées (RFC&nbsp;3161, ACME).",
            "<strong>Service de base gratuit</strong> et identique pour tous ; contribution seulement pour les engagements renforcés.",
            "<strong>Projet de statuts rigide</strong> : objet intangible, transformation lucrative interdite, clés et actifs inappropriables.",
            "<strong>Gouvernance à fonctions séparées</strong> (ETSI&nbsp;EN&nbsp;319&nbsp;401), sécurité vérifiable, journal public.",
        ],
        "pilot_h": "Ce qui tourne déjà",
        "pilot": [
            "Un service d'horodatage RFC&nbsp;3161 fonctionne en <strong>environnement d'essai public</strong>, sur un moteur en Rust publié en source ouverte. Démonstrateur : <code>demo.open-eidas.eu</code> · Code : <code>github.com/otspi/open-eidas</code>",
            "<strong>Non qualifié :</strong> les jetons émis n'ont aucune valeur juridique. Aucune qualification n'a été demandée à ce jour.",
        ],
        "road_h": "Feuille de route",
        "road": [
            ("Présentation", "aux autorités et à la recherche, pour avis"),
            ("Banc d'essai", "environnement public, politique et DPC pilotes"),
            ("Qualification", "audit et demande de statut qualifié"),
            ("Autorité TLS", "DV automatisé, OV / QWAC, WebTrust"),
            ("Cachet, signature, identité", "en parallèle"),
        ],
        "note": "Ces phases décrivent des démarches envisagées ; elles ne préjugent ni des avis des institutions, ni des décisions qui relèvent de leur seule compétence. Aucun calendrier n'est fixé.",
        "ask_h": "Nous cherchons des partenaires",
        "ask": "Hébergeurs et cloud souverain · financeurs et fondations · laboratoires de recherche · auditeurs eIDAS · éditeurs de logiciels de facturation · collectivités. Et des personnes pour tenir les rôles indépendants : officiers d'autorité, RSSI, comité des politiques de confiance.",
        "mail": "contact@otspi.org · www.otspi.org",
        "qrcap": "www.otspi.org",
        "qr": "qr-fr.svg",
        "out": "otspi-plaquette-fr.pdf",
    },
    "en": {
        "lang": "en",
        "title": "OTSPI — One-page overview",
        "kicker": "White paper · public consultation v0.9",
        "h1": "eIDAS trust services as a European digital commons",
        "lead": "OTSPI is a public-interest initiative, currently being formed as a non-profit association under the French law of 1901. It is building an open, auditable and inalienable trust service provider: time-stamping, certificates, seals, signatures and identity, through standard APIs and with no per-transaction fees.",
        "figures_h": "Why now",
        "figures": [
            ("24.12.2026", "deadline for each Member State to provide the European Digital Identity Wallet"),
            ("10 million", "economic actors in France affected by mandatory e-invoicing (broadest scope)"),
            ("≈ €10,000", "excl. VAT per year to time-stamp 15,000 documents a month, at a qualified provider's public prices"),
            ("47 days", "maximum validity of a Web certificate in 2029, down from 398 in 2025: automation becomes mandatory"),
        ],
        "problem_h": "The problem",
        "problem": [
            "<strong>280 qualified providers</strong> in the EEA, yet a single model: prior contract, per-unit pricing, proprietary interfaces, markets fragmented by country.",
            "<strong>SMEs, local authorities, universities and open source projects</strong> are in effect shut out of qualified evidence.",
            "<strong>64 %</strong> of websites rely on a single certificate authority, established outside the Union.",
        ],
        "answer_h": "Our response",
        "answer": [
            "<strong>Fully open code</strong> (EUPL&nbsp;1.2), standard APIs (RFC&nbsp;3161, ACME).",
            "<strong>Free baseline service</strong>, identical for everyone; contributions only for enhanced commitments.",
            "<strong>Entrenched draft statutes</strong>: unamendable purpose, no for-profit conversion, keys and assets beyond appropriation.",
            "<strong>Governance with segregated duties</strong> (ETSI&nbsp;EN&nbsp;319&nbsp;401), verifiable security, public log.",
        ],
        "pilot_h": "Already running",
        "pilot": [
            "An RFC&nbsp;3161 time-stamping service runs in a <strong>public test environment</strong>, on an engine written in Rust and published as open source. Demo: <code>demo.open-eidas.eu</code> · Code: <code>github.com/otspi/open-eidas</code>",
            "<strong>Not qualified:</strong> tokens issued have no legal value. No qualification has been applied for to date.",
        ],
        "road_h": "Roadmap",
        "road": [
            ("Presenting", "to authorities and researchers, for their opinion"),
            ("Test bench", "public environment, pilot policy and CPS"),
            ("Qualification", "audit and application for qualified status"),
            ("TLS authority", "automated DV, OV / QWAC, WebTrust"),
            ("Seals, signatures, identity", "in parallel"),
        ],
        "note": "These phases describe intended steps; they do not prejudge the opinions of institutions, nor decisions within their sole competence. No timetable is set.",
        "ask_h": "We are looking for partners",
        "ask": "Hosting and sovereign cloud providers · funders and foundations · research laboratories · eIDAS auditors · invoicing software vendors · local authorities. And people to hold the independent roles: authority officers, CISO, trust policy committee.",
        "mail": "contact@otspi.org · www.otspi.org/en",
        "qrcap": "www.otspi.org/en",
        "qr": "qr-en.svg",
        "out": "otspi-plaquette-en.pdf",
    },
}


def render(t):
    figures = "".join(f'<div class="fig"><b>{a}</b><span>{b}</span></div>' for a, b in t["figures"])
    bullets = lambda items: "".join(f"<li>{x}</li>" for x in items)
    road = "".join(
        f'<div class="step"><b><i>{n}</i>{a}</b>{b}</div>' for n, (a, b) in enumerate(t["road"], 1)
    )
    pilot = "".join(f"<p>{x}</p>" for x in t["pilot"])
    return f"""<!doctype html>
<html lang="{t['lang']}"><head><meta charset="utf-8"><title>{t['title']}</title>
<link rel="stylesheet" href="plaquette.css"></head>
<body>
<div class="top">
  <img src="logo.svg" alt="OTSPI">
  <span class="kicker">{t['kicker']}</span>
  <h1>{t['h1']}</h1>
  <p class="lead">{t['lead']}</p>
</div>
<div class="main">
  <h2>{t['figures_h']}</h2>
  <div class="figures">{figures}</div>
  <div class="cols">
    <div><h2>{t['problem_h']}</h2><ul>{bullets(t['problem'])}</ul></div>
    <div><h2>{t['answer_h']}</h2><ul>{bullets(t['answer'])}</ul></div>
  </div>
  <h2>{t['pilot_h']}</h2>
  <div class="pilot">{pilot}</div>
  <h2>{t['road_h']}</h2>
  <div class="road">{road}</div>
  <p class="note">{t['note']}</p>
</div>
<div class="foot">
  <div class="ask"><h3>{t['ask_h']}</h3><p>{t['ask']}</p><p class="mail">{t['mail']}</p></div>
  <div><div class="qr"><img src="{t['qr']}" alt="QR"></div><div class="qrcap">{t['qrcap']}</div></div>
</div>
</body></html>
"""


def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("Chrome ou Chromium introuvable : définir la variable d'environnement CHROME.")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        for name in ("plaquette.css", "qr-fr.svg", "qr-en.svg"):
            shutil.copy(SRC / name, work / name)
        shutil.copy(LOGO, work / "logo.svg")
        for lang, text in TEXTS.items():
            page = work / f"{lang}.html"
            page.write_text(render(text), encoding="utf-8")
            output = OUT / text["out"]
            output.unlink(missing_ok=True)
            with tempfile.TemporaryDirectory() as profile:
                cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={profile}",
                       "--no-pdf-header-footer", "--allow-file-access-from-files", f"--print-to-pdf={output}", page.as_uri()]
                if os.environ.get("CI"):
                    cmd.insert(1, "--no-sandbox")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0 or not output.is_file():
                sys.stderr.write(result.stderr)
                sys.exit(f"Échec de la génération de {output.name}")
            print(f"{output.relative_to(ROOT)} ({output.stat().st_size // 1024} Kio)")


if __name__ == "__main__":
    main()
