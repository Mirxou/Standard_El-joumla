# Configuration d'environnement pour le déploiement
# Environment Configuration for Deployment

## Fichiers d'environnement requis
## Required Environment Files

### Production

1. Créez un fichier `.env.production` à la racine du dossier `web/`
2. Copiez le contenu de `.env.production.example` dans `.env.production`
3. Remplissez les valeurs avec vos configurations de production :

```bash
# Exemple de configuration
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NODE_ENV=production
NEXT_PUBLIC_APP_URL=https://yourdomain.com
```

### Variables d'environnement importantes
### Important Environment Variables

- `NEXT_PUBLIC_API_BASE_URL` : URL de base de votre API backend en production
- `NEXT_PUBLIC_APP_URL` : URL de votre application frontend en production
- `NODE_ENV` : Doit être défini sur `production` pour le build de production

## Build de production
## Production Build

Pour créer un build de production :

```bash
cd web
npm run build
```

Le build créera un dossier `.next` optimisé pour la production.

## Démarrage en production
## Production Start

Pour démarrer l'application en mode production :

```bash
cd web
npm run start
```

## Notes importantes
## Important Notes

1. **Sécurité** : Ne commitez jamais les fichiers `.env.production` dans le dépôt Git
2. **Variables publiques** : Seules les variables préfixées par `NEXT_PUBLIC_` sont accessibles côté client
3. **API URL** : Assurez-vous que l'URL de l'API est correcte et accessible depuis le navigateur
