#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Génère les logos de assets/ à partir de leurs sources de scripts/logos/ (non déployé).

Les sources écrivent « OTSPI » et le sous-titre en texte SVG, en Ubuntu Sans. Chargé par <img>,
un SVG n'a pas accès aux polices de la page : chaque navigateur prenait la police installée
localement (Ubuntu Sans, sinon Liberation Sans, sinon celle du système) et le texte changeait de
largeur d'un poste à l'autre. Ce script remplace chaque <text> par les tracés des glyphes,
positionnés par HarfBuzz (crénage compris) comme le ferait un navigateur disposant de la police.

Prérequis : fontTools et uharfbuzz (pip install fonttools uharfbuzz), police Ubuntu Sans
variable (paquet fonts-ubuntu, ou https://github.com/canonical/Ubuntu-Sans-fonts).

    python3 scripts/build_logos.py [--police chemin/UbuntuSans[wdth,wght].ttf]
"""
import argparse
import html
import io
import re
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "scripts" / "logos"
POLICE = Path("/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf")
TITRE = "OTSPI — Open Trusted Service Provider Initiative"

TEXTE = re.compile(r"(?P<indent>[ \t]*)<text\b(?P<attrs>[^>]*)>(?P<corps>.*?)</text>", re.S)
TSPAN = re.compile(r"<tspan\b([^>]*)>(.*?)</tspan>", re.S)
ATTR = re.compile(r'([\w:-]+)="([^"]*)"')


class Police:
    def __init__(self, chemin):
        self.donnees = Path(chemin).read_bytes()
        self.instances = {}

    def instance(self, graisse):
        if graisse not in self.instances:
            ttf = instantiateVariableFont(TTFont(io.BytesIO(self.donnees)), {"wght": graisse, "wdth": 100})
            tampon = io.BytesIO()
            ttf.save(tampon)
            face = hb.Face(tampon.getvalue())
            self.instances[graisse] = (ttf, hb.Font(face), face.upem)
        return self.instances[graisse]


def segments(corps, remplissage):
    """Texte et couleur de chaque segment, espaces réduits comme le fait SVG par défaut."""
    morceaux, pos = [], 0
    for m in TSPAN.finditer(corps):
        if m.start() > pos:
            morceaux.append((corps[pos:m.start()], remplissage))
        morceaux.append((m.group(2), dict(ATTR.findall(m.group(1))).get("fill", remplissage)))
        pos = m.end()
    morceaux.append((corps[pos:], remplissage))
    texte = "".join(t for t, _ in morceaux)
    debut = len(texte) - len(texte.lstrip())
    fin = len(texte.rstrip())
    resultat, index = [], 0
    for t, couleur in morceaux:
        garde = t[max(0, debut - index): max(0, fin - index)]
        index += len(t)
        garde = html.unescape(re.sub(r"\s+", " ", garde))
        if garde:
            resultat.append((garde, couleur))
    return resultat


def en_traces(attrs, corps, police):
    a = dict(ATTR.findall(attrs))
    taille = float(a["font-size"])
    espacement = float(a.get("letter-spacing", 0))
    ttf, font, upem = police.instance(int(a.get("font-weight", 400)))
    echelle = taille / upem

    # Chaque <tspan> est mis en forme à part, comme le font les navigateurs : pas de crénage
    # entre deux segments (le « O » bleu et le « T » d'OTSPI).
    glyphes_places = []
    for texte, couleur in segments(corps, a.get("fill", "#000000")):
        tampon = hb.Buffer()
        tampon.add_str(texte)
        tampon.guess_segment_properties()
        hb.shape(font, tampon, {"kern": True, "liga": True})
        glyphes_places += [(info.codepoint, pos, couleur) for info, pos in zip(tampon.glyph_infos, tampon.glyph_positions)]

    # letter-spacing s'ajoute après chaque caractère, dernier compris, comme dans les navigateurs.
    largeur = sum(pos.x_advance * echelle + espacement for _, pos, _ in glyphes_places)
    x = float(a.get("x", 0))
    if a.get("text-anchor") == "middle":
        x -= largeur / 2
    elif a.get("text-anchor") == "end":
        x -= largeur
    y = float(a.get("y", 0))

    glyphes = ttf.getGlyphSet()
    noms = ttf.getGlyphOrder()
    parCouleur = {}
    for glyphe, pos, couleur in glyphes_places:
        stylo = SVGPathPen(glyphes, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        gx, gy = x + pos.x_offset * echelle, y - pos.y_offset * echelle
        glyphes[noms[glyphe]].draw(TransformPen(stylo, (echelle, 0, 0, -echelle, gx, gy)))
        if stylo.getCommands():
            parCouleur.setdefault(couleur, []).append(stylo.getCommands())
        x += pos.x_advance * echelle + espacement
    return [(couleur, "".join(d)) for couleur, d in parCouleur.items()]


def convertir(source, police):
    svg = source.read_text(encoding="utf-8")

    def remplacer(m):
        indent = m.group("indent")
        return "\n".join(f'{indent}<path fill="{c}" d="{d}" />' for c, d in en_traces(m.group("attrs"), m.group("corps"), police))

    svg = TEXTE.sub(remplacer, svg)
    # Le texte ayant disparu, le nom est porté par un titre (lu si le SVG est ouvert seul).
    svg = re.sub(r"(<svg\b[^>]*?)>", rf'\1 role="img" aria-label="{TITRE}">\n  <title>{TITRE}</title>', svg, count=1)
    return svg


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--police", default=POLICE, help="police Ubuntu Sans variable")
    args = parser.parse_args()
    if not Path(args.police).is_file():
        sys.exit(f"Police introuvable : {args.police} (option --police)")
    police = Police(args.police)
    for source in sorted(SOURCES.glob("*.svg")):
        cible = ROOT / "assets" / source.name
        cible.write_text(convertir(source, police), encoding="utf-8")
        print(f"{cible.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
