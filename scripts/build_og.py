#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Génère les images de partage de l'accueil (1200 × 630) : assets/og/og-fr.png et og-en.png.

L'image est composée en HTML puis capturée par Chrome ou Chromium en mode headless ; la variable
d'environnement CHROME permet d'imposer le binaire. Le titre et le sous-titre doivent rester
identiques à ceux du hero de la page d'accueil.

Usage :
    python3 scripts/build_og.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "og"
LOGO = ROOT / "assets" / "logo-horizontal-transparent-dark.svg"

TEXTS = {
    "fr": ("Livre blanc", "Et si la confiance numérique européenne devenait un bien commun&nbsp;?",
           "La preuve qualifiée eIDAS, ouverte, automatisable et sans péage. Un pilote tourne déjà.",
           "Consultation publique · appel à partenaires"),
    "en": ("White paper", "What if European digital trust became a shared resource?",
           "Qualified eIDAS proof, open, automatable and toll-free. A pilot already runs.",
           "Public consultation · call for partners"),
}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:1200px;height:630px;overflow:hidden}
body{font-family:"Noto Sans","Open Sans",system-ui,sans-serif;color:#fff;
background:radial-gradient(circle at 92% 8%,#052a80 0,transparent 45%),linear-gradient(135deg,#111d3a,#0a2a6b);position:relative}
.logo{position:absolute;left:72px;top:64px;height:52px}
.badge{position:absolute;left:72px;top:140px;padding:8px 22px;border:2px solid #b8921a;border-radius:999px;
color:#ffd000;font-weight:700;font-size:24px;letter-spacing:.14em;text-transform:uppercase}
h1{position:absolute;left:72px;top:212px;width:1056px;margin:0;font-size:62px;line-height:1.12;font-weight:700}
.sub{position:absolute;left:72px;top:462px;width:1000px;font-size:27px;line-height:1.35;color:#c9d6f2}
.foot{position:absolute;left:72px;bottom:44px;font-size:24px;color:#a9bbe0}
.url{position:absolute;right:72px;bottom:44px;font-size:26px;font-weight:700}
.bar{position:absolute;left:0;bottom:0;height:12px;width:70%;background:#0033a0}
.bar2{position:absolute;right:0;bottom:0;height:12px;width:30%;background:#ffd000}
</style></head><body>
<img class="logo" src="logo.svg" alt="">
<div class="badge">{{badge}}</div>
<h1>{{title}}</h1>
<div class="sub">{{sub}}</div>
<div class="foot">{{foot}}</div><div class="url">otspi.org</div>
<div class="bar"></div><div class="bar2"></div>
</body></html>"""


def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("Chrome ou Chromium introuvable : définir la variable d'environnement CHROME.")


def main():
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        shutil.copy(LOGO, work / "logo.svg")
        for lang, (badge, title, sub, foot) in TEXTS.items():
            page = work / f"{lang}.html"
            html = PAGE
            for key, value in (("badge", badge), ("title", title), ("sub", sub), ("foot", foot)):
                html = html.replace("{{" + key + "}}", value)
            page.write_text(html, encoding="utf-8")
            output = OUT / f"og-{lang}.png"
            with tempfile.TemporaryDirectory() as profile:
                cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                       "--allow-file-access-from-files", "--window-size=1200,630", f"--screenshot={output}", page.as_uri()]
                if os.environ.get("CI"):
                    cmd.insert(1, "--no-sandbox")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0 or not output.is_file():
                sys.stderr.write(result.stderr)
                sys.exit(f"Échec de la génération de {output.name}")
            print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()
