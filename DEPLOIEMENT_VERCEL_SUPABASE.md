# Déployer le backend Tangawisa sur Vercel et Supabase

## 1. Préparer Supabase

Le projet `tangawisadb` doit contenir les tables de `scripts/supabase_schema.sql` et le durcissement de `scripts/supabase_hardening.sql`.

Créer ensuite une clé serveur Supabase dédiée et préparer Storage :

```powershell
$env:SUPABASE_URL="https://udrfjcjqursyprshownx.supabase.co"
$env:SUPABASE_SECRET_KEY="sb_secret_xxxxx"
$env:SUPABASE_STORAGE_BUCKET="site-presentation"
python scripts/setup_supabase_storage.py
```

## 2. Configurer le projet Vercel

Dans Vercel :

1. importer le dépôt Tangawisa ;
2. choisir `backend` comme **Root Directory** ;
3. laisser Vercel détecter FastAPI dans `app/main.py` ;
4. ajouter les variables ci-dessous pour Production et Preview.

```env
APP_NAME=Tangawisa API
APP_ENV=production
APP_VERSION=0.1.0
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql://tangawisa_backend.udrfjcjqursyprshownx:VOTRE_MOT_DE_PASSE@aws-1-eu-west-1.pooler.supabase.com:6543/postgres
JWT_SECRET_KEY=UNE_CLE_ALEATOIRE_DE_32_CARACTERES_MINIMUM
CORS_ORIGINS=https://votre-frontend.vercel.app,https://votre-domaine.com
BOOTSTRAP_DATABASE=false
SEED_DEVELOPMENT_DATA=false
DISABLE_DATABASE_POOLING=true
MEDIA_STORAGE_BACKEND=supabase
SUPABASE_URL=https://udrfjcjqursyprshownx.supabase.co
SUPABASE_SECRET_KEY=sb_secret_xxxxx
SUPABASE_STORAGE_BUCKET=site-presentation
```

Ne pas ajouter ces valeurs dans `.env.example`, Git ou une application cliente.

## 3. Déployer

Avec l’intégration Git, pousser la branche puis vérifier le Preview avant promotion.

Avec le CLI Vercel :

```powershell
vercel link
vercel env pull .env.local --environment=production
vercel build --prod
vercel deploy --prebuilt --prod
```

## 4. Vérifier le déploiement

Remplacer `<URL>` par l’URL Vercel :

```powershell
Invoke-RestMethod https://<URL>/health
Invoke-RestMethod https://<URL>/health/ready
Invoke-RestMethod https://<URL>/api/v1/system/info
Invoke-RestMethod https://<URL>/api/v1/marketplace/catalog
```

Vérifier également :

- `https://<URL>/docs` ;
- inscription puis connexion d’un compte de test ;
- upload JPEG/PNG/WebP dans l’administration ;
- présence de l’image dans le bucket `site-presentation` ;
- absence d’erreurs dans les Runtime Logs Vercel et les Advisors Supabase.

## 5. Règles de production

- ne pas activer le seed de développement ;
- ne pas utiliser SQLite sur Vercel ;
- ne pas utiliser le super-rôle PostgreSQL `postgres` pour l’application ;
- séparer les clés Supabase Preview et Production si les environnements utilisent des bases différentes ;
- faire une migration Supabase avant de promouvoir le même artefact Vercel en production.
