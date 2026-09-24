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
| `mentions-legales.html` | Mentions légales et données personnelles |
| `style.css` | Feuille de style |
| `script.js` | Menu de navigation mobile |
| `.htaccess` | HTTPS, domaine canonique, en-têtes de sécurité, cache |
| `assets/` | Logos et favicons OTSPI |
| `.github/workflows/deploy.yml` | Déploiement SFTP vers Infomaniak à chaque push sur `main` |

Le script d'amorçage en ligne (`document.documentElement.classList.add('js')`) est autorisé dans la CSP par son empreinte SHA-256.
Toute modification de ce script impose de recalculer l'empreinte dans `.htaccess` :

```sh
printf '%s' "document.documentElement.classList.add('js');" | openssl dgst -sha256 -binary | base64
```

## Déploiement

Le site est déployé par SFTP (`lftp mirror`) vers Infomaniak à chaque push sur `main`.
La clé d'hôte du serveur est vérifiée strictement.

Secrets et variables du dépôt (**Settings > Secrets and variables > Actions**) :

| Nom | Type | Description |
|---|---|---|
| `SFTP_HOST` | secret | Hôte SSH/SFTP de l'hébergement Infomaniak |
| `SFTP_PORT` | secret, optionnel | Port SSH (22 par défaut) |
| `SFTP_USERNAME` | secret | Utilisateur SSH/SFTP |
| `SFTP_PASSWORD` | secret | Mot de passe SSH/SFTP |
| `SFTP_KNOWN_HOSTS` | secret | Ligne(s) `known_hosts` du serveur (`ssh-keyscan -p 22 <hôte>`, empreinte vérifiée dans le Manager) |
| `SFTP_SERVER_DIR` | variable | Répertoire du site www.otspi.org sur l'hébergement |

Côté Infomaniak : activer l'accès SSH, rattacher `www.otspi.org` et `otspi.org` au répertoire du site et activer le certificat SSL Let's Encrypt.

## Aperçu local

```sh
python3 -m http.server 8000
```

## Licences

- Code du site : [EUPL 1.2](LICENSE)
- Contenus rédactionnels : [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.fr)
