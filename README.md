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
3. Relire la liste générée dans `manifeste.html`, puis commiter et pousser.

Les exports CSV et le fichier de retraits contiennent des données personnelles : ils ne doivent jamais être commités (`.gitignore`).

## Aperçu local

```sh
python3 -m http.server 8000
```

## Licences

- Code du site : [EUPL 1.2](LICENSE)
- Contenus rédactionnels : [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.fr)
