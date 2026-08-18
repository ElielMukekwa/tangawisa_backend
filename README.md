Socle backend FastAPI pour Tangawisa.

## Objectif de cette couche

Cette premiere couche pose les fondations de production :

- configuration centralisee,
- connexion MySQL via SQLAlchemy,
- structure modulaire FastAPI,
- modeles de base Tangawisa,
- endpoints systeme pour verification et brancheme

## Déploiement Vercel

Le backend expose une entrée serverless dans `api/index.py` et `vercel.json`
redirige toutes les routes vers l'application FastAPI.

Variables à définir dans Vercel :

- `APP_ENV=production`
- `DATABASE_URL=mysql+pymysql://user:password@host:3306/database`
- `JWT_SECRET_KEY=<secret-long-et-unique>`
- `CORS_ORIGINS=https://votre-front.vercel.app,https://votre-domaine.com`
- `SEED_DEVELOPMENT_DATA=false`

Sans `DATABASE_URL`, Vercel utilise une base SQLite temporaire dans `/tmp`.
Elle permet de démarrer et tester `/health`, mais elle n'est pas persistante :
pour un vrai système scolaire en production, utiliser une base externe MySQL.
