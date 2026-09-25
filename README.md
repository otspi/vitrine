# OTSPI — Site vitrine www.otspi.org

Site vitrine de l'**Open Trusted Service Provider Initiative (OTSPI)**, construit autour du livre blanc
*« Une infrastructure de services de confiance qualifiés d'utilité publique pour eIDAS 2.0 »*.
Il s'adresse aux partenaires potentiels : hébergeurs, financeurs, laboratoires, auditeurs, éditeurs et administrations.

- **Site** : [www.otspi.org](https://www.otspi.org)
- **Livre blanc (source de référence)** : [about.otspi.org/livre-blanc](https://about.otspi.org/livre-blanc/) — dépôt [otspi/organisation](https://github.com/otspi/organisation)
- **Hébergement** : Infomaniak (Genève, Suisse)

## Principes

- HTML et CSS statiques, sans framework ni étape de construction.
- Aucune ressource externe, aucun cookie, aucun traceur ; polices système.
- Thèmes clair et sombre (`prefers-color-scheme`), mise en page adaptée aux mobiles.
- Politique de sécurité du contenu stricte (`.htaccess`).

## Structure

| Fichier | Rôle |
|---|---|
| `index.html` | Page d'accueil : repères, constat, réponse, services, sécurité, statuts, feuille de route, appel à partenaires |
| `manifeste.html` | Manifeste pour une identité numérique libre et ouverte et liste des signataires |
| `mentions-legales.html` | Mentions légales et données personnelles |
| `actualites.html`, `en/news.html` | Actualités, avec flux Atom `feed.xml` et `en/feed.xml` |
| `404.html`, `robots.txt`, `sitemap.xml` | Page d'erreur bilingue et fichiers de référencement |
| `en/` | Version anglaise : `index.html`, `manifesto.html`, `legal-notice.html` (balises `hreflang`, la version française fait foi) |
| `scripts/signataires.py` | Génération de la liste publique des signataires (non déployé) |
| `style.css` | Feuille de style |
| `script.js` | Menu de navigation mobile |
| `.htaccess` | HTTPS, domaine canonique, en-têtes de sécurité, cache |
| `assets/` | Logos et favicons OTSPI |
| `.github/workflows/deploy.yml` | Déploiement FTP vers Infomaniak à chaque push sur `main` |

Le script d'amorçage en ligne (`document.documentElement.classList.add('js')`) est autorisé dans la CSP par son empreinte SHA-256.
Toute modification de ce script impose de recalculer l'empreinte dans `.htaccess` :

```sh
printf '%s' "document.documentElement.classList.add('js');" | openssl dgst -sha256 -binary | base64
```

## Déploiement

Le site est déployé par FTP (`lftp mirror`) vers Infomaniak à chaque push sur `main`.
L'hébergement n'expose que le FTP sans TLS ; le compte utilisé est cantonné au seul répertoire du site www.otspi.org.

Secrets et variables du dépôt (**Settings > Secrets and variables > Actions**) :

| Nom | Type | Description |
|---|---|---|
| `FTP_HOST` | secret | Hôte FTP de l'hébergement Infomaniak |
| `FTP_USERNAME` | secret | Utilisateur FTP du site www.otspi.org |
| `FTP_PASSWORD` | secret | Mot de passe FTP |
| `FTP_SERVER_DIR` | variable, optionnelle | Répertoire cible (racine du compte, `./`, par défaut) |

Côté Infomaniak : activer le certificat SSL Let's Encrypt pour `www.otspi.org` et `otspi.org`.

## Manifeste : recueil des signatures

Les signatures sont recueillies sur un formulaire [Framaforms](https://framaforms.org) (Framasoft) :
<https://framaforms.org/manifeste-pour-une-identite-numerique-libre-et-ouverte-1790280399>
(nœud 1538128, compte de l'association).

### Champs du formulaire

| Libellé | Clé (Form Key) | Type | Obligatoire | Remarque |
|---|---|---|---|---|
| Prénom | `prenom` | texte | oui | |
| Nom | `nom` | texte | oui | |
| Adresse e-mail | `adresse_e_mail` | courriel | oui | jamais publiée |
| Fonction | `fonction` | texte | non | |
| Organisation | `organisation` | texte | non | |
| Publication | `publication` | case à cocher | non | accord pour figurer dans la liste publique |
| Suites | `suites` | case à cocher | non | être informé·e des suites |
| Consentement | `consentement` | case à cocher | oui | traitement des données (mentions légales) |

Résultats non publics. Le script s'appuie sur les **clés** : ne pas les modifier.

**Expiration** : Framaforms limite la durée de vie d'un formulaire à 6 mois (échéance actuelle : 24 mars 2027).
Avant l'échéance, prolonger en modifiant le formulaire (« Modifier » > date d'expiration).
Le formulaire est limité à 5 000 réponses.

### Mise à jour de la liste publique

1. Framaforms > Résultats > Télécharger : format **Texte délimité** (tabulation), en-têtes **Form Key**,
   liste des options **Compact**. Enregistrer l'export hors du dépôt.
2. `python3 scripts/signataires.py ~/export-framaforms.csv --exclure ~/retraits.txt`
   (`retraits.txt` : adresses à exclure — retraits de signature et signatures douteuses, une par ligne).
3. Relire la liste générée dans `manifeste.html` et `en/manifesto.html` (mises à jour ensemble), puis commiter et pousser.

Les **signataires de base** (`scripts/signataires-base.json`, consentement recueilli directement) sont toujours ajoutés à la liste. Sans export, `python3 scripts/signataires.py` régénère la liste à partir de ces seuls signataires.

### Rafraîchissement automatique (cron)

`scripts/refresh-signataires.sh` fait les étapes 2 et 3 à partir du dernier CSV déposé dans `~/otspi-export/` (dossier hors dépôt, droits 700) : si l'export ou `retraits.txt` a changé, il régénère la liste, committe uniquement `manifeste.html` et `en/manifesto.html`, puis pousse (le déploiement suit). Il s'arrête sans rien faire si le dépôt n'est pas sur `main` ou contient des modifications en cours. Seul le téléchargement de l'export Framaforms reste manuel (l'interface exige une session connectée). Le journal est `~/otspi-export/refresh.log`.

```
17 8 * * * /chemin/vers/otspi-vitrine/scripts/refresh-signataires.sh >> ~/otspi-export/refresh.log 2>&1
```

Les exports CSV et le fichier de retraits contiennent des données personnelles : ils ne doivent jamais être commités (`.gitignore`).

## Plaquette d'une page

`python3 scripts/build_plaquette.py` régénère `assets/docs/otspi-plaquette-fr.pdf` et `otspi-plaquette-en.pdf` (Chrome ou Chromium requis ; sources dans `scripts/plaquette/`). Les chiffres sont ceux de la page d'accueil : les mettre à jour ensemble.

## Mesure d'audience (non activée)

Le site n'utilise aucun outil de mesure d'audience. Si une mesure devient utile, la voie la plus sobre est **l'analyse des journaux d'accès du serveur** (aucun script, aucun cookie), avec un outil comme GoAccess. Préalable : vérifier qu'Infomaniak met les journaux d'accès à disposition pour cette formule d'hébergement.

Conditions retenues (recommandations de la CNIL pour la mesure d'audience exemptée de consentement) : finalité limitée à la mesure d'audience pour le compte de l'éditeur, statistiques agrégées uniquement, aucun croisement avec d'autres traitements ni suivi entre sites, conservation des journaux limitée (25 mois au plus), information dans les mentions légales.

**Avant d'activer**, remplacer la phrase « n'utilise aucun outil de mesure d'audience » des mentions légales (FR et EN) et ajouter :

> **Mesure d'audience.** Pour connaître la fréquentation du site (pages consultées, provenance approximative), les journaux d'accès du serveur sont analysés de façon agrégée, sans cookie ni traceur. Cette analyse repose sur l'intérêt légitime de l'éditeur à mesurer l'audience de son site ; elle ne sert à aucune autre finalité, n'est croisée avec aucune autre donnée et n'est pas transmise à des tiers. Les journaux sont conservés au plus 25 mois. Vous pouvez vous opposer à ce traitement en écrivant à contact@otspi.org.

> **Audience measurement.** To understand how the site is used (pages viewed, approximate origin), server access logs are analysed in aggregate, without cookies or trackers. This relies on the publisher's legitimate interest in measuring the audience of its site; it serves no other purpose, is not combined with any other data and is not shared with third parties. Logs are kept for at most 25 months. You may object to this processing by writing to contact@otspi.org.

Ces textes sont un projet, à faire valider avant publication.

## Contrôle des liens

`python3 scripts/check_links.py . --ignore scripts/links-ignore.txt` vérifie les liens externes ; un workflow le lance chaque mois et ouvre un ticket si des liens sont cassés. Les sites qui refusent les robots (403) sont listés « à vérifier » sans faire échouer le contrôle.

## Sécurité

`/.well-known/security.txt` (RFC 9116) indique où signaler une vulnérabilité. **Sa date `Expires` doit être renouvelée avant le 25 mars 2027** ; passé cette date, le fichier est considéré comme périmé.

## Publier une actualité

Ajouter l'entrée **en tête** de `actualites.html` et `en/news.html`, ainsi que dans `feed.xml` et `en/feed.xml`
(identifiant stable, date `updated`, résumé), puis mettre à jour la date `updated` du flux et `lastmod` dans `sitemap.xml`.

## Aperçu local

```sh
python3 -m http.server 8000
```

## Licences

- Code du site : [EUPL 1.2](LICENSE)
- Contenus rédactionnels : [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.fr)
