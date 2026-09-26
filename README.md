# OTSPI — Site vitrine www.otspi.org

Site vitrine de l'**Open Trusted Service Provider Initiative (OTSPI)**, construit autour du livre blanc
*« Une infrastructure de services de confiance qualifiés d'utilité publique pour eIDAS 2.0 »*.
Il s'adresse aux partenaires potentiels : hébergeurs, financeurs, laboratoires, auditeurs, éditeurs et administrations.

- **Site** : [www.otspi.org](https://www.otspi.org)
- **Livre blanc (source de référence)** : [about.otspi.org/livre-blanc](https://about.otspi.org/livre-blanc/) — dépôt [otspi/organisation](https://github.com/otspi/organisation)
- **Hébergement** : o2switch (Clermont-Ferrand, France), depuis le 26 septembre 2026

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
| `scripts/build_og.py` | Génération des images de partage de l'accueil (non déployé) |
| `style.css` | Feuille de style |
| `script.js` | Menu de navigation mobile |
| `.htaccess` | HTTPS, domaine canonique, en-têtes de sécurité, cache |
| `assets/` | Logos et favicons OTSPI |
| `.github/workflows/deploy.yml` | Déploiement FTPS vers o2switch à chaque push sur `main` |

Le script d'amorçage en ligne (`document.documentElement.classList.add('js')`) est autorisé dans la CSP par son empreinte SHA-256.
Toute modification de ce script impose de recalculer l'empreinte dans `.htaccess` :

```sh
printf '%s' "document.documentElement.classList.add('js');" | openssl dgst -sha256 -binary | base64
```

## Déploiement

Le site est déployé en FTPS (`lftp mirror`, TLS obligatoire, certificat vérifié) vers o2switch à chaque push sur `main`, avec un compte FTP cantonné au répertoire du site.
Secrets et variables du dépôt (**Settings > Secrets and variables > Actions**) :

| Nom | Type | Description |
|---|---|---|
| `O2_FTP_HOST` | variable | Hôte FTPS d'o2switch |
| `O2_FTP_USERNAME` | secret | Compte FTP dédié au répertoire du site |
| `O2_FTP_PASSWORD` | secret | Mot de passe de ce compte |

Côté o2switch (cPanel) : le domaine `otspi.org` (répertoire du site) couvre aussi `www.otspi.org` ; `otspi.com`, `otspi.eu` et `otspi.fr` pointent sur le même répertoire et sont redirigés par le `.htaccess`. Les certificats Let's Encrypt sont émis dans le module « Let's Encrypt™ SSL » et renouvelés automatiquement. Le routage des e-mails de ces domaines est « distant » : la messagerie reste chez Infomaniak.

## Manifeste : recueil des signatures

Les signatures sont recueillies par une petite application PHP hébergée chez o2switch (France), dont le code est dans le dépôt `otspi-signatures` : <https://manifesto-sign.otspi.org/>. La page du manifeste renvoie vers ce formulaire. Le parcours : formulaire, e-mail de confirmation (double consentement), confirmation, puis lien de retrait qui supprime tout. Rien n'est publié avant confirmation, et seules les signatures dont l'auteur a consenti à la publication figurent dans la liste.

L'application expose la liste publique en JSON, sans adresse e-mail : <https://manifesto-sign.otspi.org/signataires.php>.

### Mise à jour de la liste publique

`python3 scripts/signataires.py --json https://manifesto-sign.otspi.org/signataires.php` régénère la liste dans `manifeste.html` et `en/manifesto.html` (mises à jour ensemble). Le total compte aussi les signatures dont l'auteur n'a pas consenti à la publication, qui ne sont jamais listées. Les **signataires de base** (`scripts/signataires-base.json`, consentement recueilli directement) sont toujours ajoutés.

Signatures historiques : le script accepte encore un export CSV Framaforms (`python3 scripts/signataires.py export.csv --exclure retraits.txt`), utile seulement si des signatures y ont été recueillies avant la migration.

### Rafraîchissement automatique (cron)

`scripts/refresh-signataires.sh` télécharge la liste JSON, et si elle a changé (ou si un CSV historique ou `retraits.txt` de `~/otspi-export/` a changé), il régénère les pages, committe uniquement `manifeste.html` et `en/manifesto.html`, puis pousse (le déploiement suit). Il abandonne sans rien modifier si la liste est inaccessible ou invalide, si le dépôt n'est pas sur `main` ou s'il contient des modifications en cours. Le journal est `~/otspi-export/refresh.log`.

```
17 8 * * * /chemin/vers/otspi-vitrine/scripts/refresh-signataires.sh >> ~/otspi-export/refresh.log 2>&1
```

Le retrait d'une signature dans l'application supprime la signature à la source ; la liste publique du site est actualisée au prochain passage du cron (au plus 24 heures). Les exports CSV et le fichier de retraits contiennent des données personnelles : ils ne doivent jamais être commités (`.gitignore`).

## Images de partage

`python3 scripts/build_og.py` régénère les quatre images de partage de `assets/og/` (`og-fr.png`, `og-en.png` pour l'accueil, `og-manifeste.png`, `og-manifesto.png` pour le manifeste ; 1200 × 630 px, utilisées par les balises Open Graph et Twitter ; Chrome ou Chromium requis). Les textes de l'accueil doivent rester alignés sur le hero de la page d'accueil, ceux du manifeste sur la page du manifeste. Les réseaux sociaux mettent les aperçus en cache : après un changement, forcer le rafraîchissement depuis leurs outils de débogage.

## Plaquette d'une page

`python3 scripts/build_plaquette.py` régénère `assets/docs/otspi-plaquette-fr.pdf` et `otspi-plaquette-en.pdf` (Chrome ou Chromium requis ; sources dans `scripts/plaquette/`). Les chiffres sont ceux de la page d'accueil : les mettre à jour ensemble.

## Mesure d'audience

Les sites d'OTSPI (vitrine, portail, démonstrateur, formulaire de signature) mesurent leur audience avec **Matomo Tag Manager**, conteneur `GR7y5y3d` de l'instance `stats.otspi.org` (o2switch, France), configuré pour l'exemption de consentement de la CNIL. Chaque site charge le même fichier `analytics.js` (ici `assets/analytics.js`, avec `defer`, sur toutes les pages FR et EN) : pas de script en ligne, que la politique de sécurité (`.htaccess`) interdit ; elle autorise `https://stats.otspi.org` dans `script-src`, `img-src` et `connect-src`.

### Configuration obligatoire (exemption CNIL)

La conformité ne dépend pas du code du site mais de Matomo. À vérifier après chaque publication du conteneur :

- **Tag Manager**, variable « Matomo Configuration » : « Disable cookies » et « Enable Do Not Track » cochés, suivi entre domaines désactivé, aucun identifiant utilisateur ni dimension personnalisée. Ne pas ajouter de balise « Custom HTML » ni de balise tierce.
- **Administration > Confidentialité** : « Forcer le suivi sans cookie » (filet de sécurité si le conteneur est mal réglé), adresses IP tronquées, suppression des anciennes données brutes à 180 jours, rapports agrégés conservés au plus 25 mois.
- **Aucune donnée personnelle dans les URL** : le formulaire de signature ne charge pas le traceur sur les pages de confirmation, de retrait et de modération, dont l'adresse porte un jeton.

Contrôle : dans le navigateur, aucun cookie `_pk_*` ni `mtm_*` ne doit apparaître après une visite ; le lien de retrait (*opt-out*) figure dans les mentions légales (FR et EN).

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
