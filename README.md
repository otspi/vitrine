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

## Mesure d'audience (non activée)

Le site n'utilise aucun outil de mesure d'audience. **Choix retenu : Matomo configuré selon le guide de la CNIL** (mesure d'audience exemptée de consentement). Matomo est l'un des outils que la CNIL a évalués ; Plausible et Umami ne figurent pas nommément dans sa liste, ce qui ne permet pas de garantir l'exemption.

### Deux hébergements possibles

| | Matomo Cloud | Matomo auto-hébergé |
|---|---|---|
| Mise en place | Compte à créer, service payant après l'essai | Application PHP et base MySQL à installer sur un hébergement (Infomaniak, par exemple sur `stats.otspi.org`) |
| Données | Chez le prestataire, sous-traitant au sens du RGPD (contrat de sous-traitance et lieu d'hébergement à vérifier) | Chez l'hébergeur du site, sans tiers supplémentaire |
| Maintenance | Aucune | Mises à jour de sécurité à assurer |

### Configuration obligatoire (exemption CNIL)

Dans Matomo : *Administration > Confidentialité > Conformité*, activer « Appliquer la conformité dès que possible » pour le site. Cela impose notamment : adresse IP tronquée, conservation limitée à 759 jours, aucun identifiant utilisateur, paramètres de campagne retirés, référent réduit au domaine, journal des visites et profils désactivés, cartes de chaleur et enregistrement de sessions désactivés. À vérifier ensuite à la main : aucun suivi entre domaines, aucun événement personnalisé hors présence de page, usage de fonctionnalité et performance, aucune donnée personnelle dans les URL.

### Mise en œuvre sur le site

1. Créer l'instance Matomo et le site `www.otspi.org` ; relever l'URL de l'instance et l'identifiant du site.
2. Ajouter un fichier `assets/matomo.js` (le code de suivi de Matomo, sans script en ligne : la politique de sécurité du site l'interdit) et le charger avec `defer` sur toutes les pages, FR et EN.
3. Adapter la politique de sécurité (`.htaccess`) : autoriser le domaine de l'instance dans `script-src` et `connect-src` (et `img-src` si l'image de suivi est utilisée).
4. Mettre à jour les mentions légales (FR et EN), qui affirment aujourd'hui l'absence de tout outil de mesure d'audience et de toute ressource tierce, et ajouter le lien de retrait (*opt-out*) fourni par Matomo.
5. Mettre à jour la page de transparence sur les [hébergements](https://about.otspi.org/reunions/hebergements/) si l'instance n'est pas hébergée chez Infomaniak.
6. Contrôler avec Lighthouse (les scores ne doivent pas baisser) et dans le navigateur qu'**aucun cookie** n'est déposé.

### Texte de mentions légales (projet, à faire valider avant publication)

> **Mesure d'audience.** Pour connaître la fréquentation du site (pages consultées, provenance approximative), l'éditeur utilise Matomo, configuré pour être exempté de consentement selon les recommandations de la CNIL : aucun cookie ni identifiant n'est déposé, les adresses IP sont tronquées, seules des statistiques agrégées sont produites et elles ne sont ni croisées avec d'autres données ni transmises à des tiers à d'autres fins. Les données sont conservées au plus 25 mois. Vous pouvez vous opposer à cette mesure ici : [lien de retrait] ou en écrivant à contact@otspi.org.

> **Audience measurement.** To understand how the site is used (pages viewed, approximate origin), the publisher uses Matomo, configured to be exempt from consent under CNIL guidance: no cookie or identifier is set, IP addresses are truncated, only aggregated statistics are produced and they are neither combined with other data nor shared with third parties for other purposes. Data is kept for at most 25 months. You may object to this measurement here: [opt-out link] or by writing to contact@otspi.org.

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
