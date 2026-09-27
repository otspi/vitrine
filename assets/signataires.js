// SPDX-License-Identifier: EUPL-1.2
// Liste des signataires du manifeste, à jour en direct : lit la liste publique de l'application de signature
// (attribut data-source de la section des signataires : signatures confirmées ET validées par l'administration, sans adresse
// e-mail) et les signataires de base (assets/signataires-base.json), puis réécrit le compteur et la liste avec
// le même rendu que scripts/signataires.py. En cas d'échec, la liste générée dans la page reste affichée.
//
// Les champs sont libres : ils ne sont insérés qu'en texte (textContent, jamais innerHTML) et toute entrée
// anormale (type, longueur, balise, lien, caractère de contrôle ou bidirectionnel) est comptée sans être listée.
'use strict';

(() => {
  const section = document.querySelector('section[data-source]');
  const count = section && section.querySelector('.signatures-count');
  const source = section && section.dataset.source;
  if (!count || !source) {
    return;
  }
  const en = document.documentElement.lang === 'en';
  const baseUrl = new URL('signataires-base.json', document.currentScript.src);

  const FORBIDDEN = /[<>]|:\/\/|www\.|[\u0000-\u001f\u007f-\u009f؜​‎‏‪-‮⁠-⁩﻿]/i;
  const text = (value, max) => typeof value === 'string' && value.length <= max && !FORBIDDEN.test(value);
  const valid = (s) => s !== null && typeof s === 'object'
    && text(s.prenom, 80) && text(s.nom, 80) && s.nom.trim() !== ''
    && text(s.fonction ?? '', 120) && text(s.fonction_en ?? '', 120) && text(s.organisation ?? '', 120);
  const normalize = (value) => value.replace(/\s+/g, ' ').trim().toLowerCase();
  const nameKey = (s) => normalize(`${s.prenom} ${s.nom}`);
  const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

  const element = (tag, content, className) => {
    const node = document.createElement(tag);
    node.textContent = content;
    if (className) {
      node.className = className;
    }
    return node;
  };

  const counter = (total, shown) => {
    if (en) {
      const tail = shown === total
        ? (total === 1 ? "published with the author's consent." : "all published with their authors' consent.")
        : `${shown} of which ${shown !== 1 ? 'are' : 'is'} published with their authors' consent.`;
      return ` signature${total !== 1 ? 's' : ''}, ${tail}`;
    }
    const tail = shown === total
      ? (total === 1 ? "publiée avec l'accord de son auteur." : "toutes publiées avec l'accord de leurs auteurs.")
      : `dont ${shown} publiée${shown > 1 ? 's' : ''} avec l'accord de leurs auteurs.`;
    return ` signature${total > 1 ? 's' : ''}, ${tail}`;
  };

  const render = (listed, anonymous, base) => {
    // Un signataire de base remplace une signature du formulaire au même nom.
    const baseKeys = new Set(base.map(nameKey));
    const people = listed.filter((s) => !baseKeys.has(nameKey(s))).concat(base)
      .sort((a, b) => compare(a.nom.toLowerCase(), b.nom.toLowerCase()) || compare(a.prenom.toLowerCase(), b.prenom.toLowerCase()));
    const total = people.length + anonymous;
    count.replaceChildren(element('strong', String(total)), document.createTextNode(counter(total, people.length)));

    let list = section.querySelector('.signatures-list');
    if (people.length === 0) {
      list?.remove();
      return;
    }
    if (!list) {
      list = document.createElement('ul');
      list.className = 'signatures-list';
      count.after(list);
    }
    list.replaceChildren(...people.map((s) => {
      const role = en && s.fonction_en ? s.fonction_en : (s.fonction ?? '');
      const quality = [role, s.organisation ?? ''].filter(Boolean).join(', ');
      const item = document.createElement('li');
      item.append(element('strong', [s.prenom, s.nom].filter(Boolean).join(' ')));
      if (quality) {
        item.append(element('span', quality, 'sig-quality'));
      }
      return item;
    }));
  };

  const load = (url, options) => fetch(url, options).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  });

  Promise.all([load(source, { credentials: 'omit', referrerPolicy: 'no-referrer' }), load(baseUrl)])
    .then(([feed, base]) => {
      if (!feed || !Array.isArray(feed.signataires) || !Number.isInteger(feed.total) || !Array.isArray(base)) {
        return;
      }
      const listed = feed.signataires.filter(valid);
      // Signatures confirmées non publiées (choix de l'auteur) ou entrées écartées : comptées, jamais listées.
      render(listed, Math.max(0, feed.total - listed.length), base.filter(valid));
    })
    .catch(() => {});
})();
