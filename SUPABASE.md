# Supabase pour Tangawisa

Projet actuellement associé :

- nom : `tangawisadb` ;
- référence : `udrfjcjqursyprshownx` ;
- région : `eu-west-1` ;
- URL API : `https://udrfjcjqursyprshownx.supabase.co`.

## Schéma PostgreSQL

Pour un projet vide, exécuter `scripts/supabase_schema.sql` dans le SQL Editor Supabase.

Pour une base Tangawisa existante, `scripts/supabase_hardening.sql` :

- crée le rôle applicatif `tangawisa_backend` sans mot de passe dans le code ;
- accorde uniquement les droits nécessaires au backend ;
- ferme l’accès direct des rôles Data API `anon` et `authenticated` ;
- active RLS et crée une politique dédiée sur chaque table ;
- sécurise le `search_path` de la fonction `set_updated_at`.

Le mot de passe du rôle est un secret d’infrastructure. Il doit être défini dans Supabase puis uniquement stocké dans les variables Vercel.

## Connexion Vercel

Utiliser le pooler transactionnel Supabase :

```env
DATABASE_URL=postgresql://tangawisa_backend.udrfjcjqursyprshownx:VOTRE_MOT_DE_PASSE@aws-1-eu-west-1.pooler.supabase.com:6543/postgres
DISABLE_DATABASE_POOLING=true
```

Le backend ajoute automatiquement `sslmode=require`. `NullPool` est utilisé sur Vercel pour laisser Supavisor gérer les connexions serverless.

## Supabase Storage

Créer une clé `sb_secret_...` dédiée au backend dans Supabase. Ne jamais utiliser cette clé dans Flutter, le frontend ou Git.

Variables requises :

```env
SUPABASE_URL=https://udrfjcjqursyprshownx.supabase.co
SUPABASE_SECRET_KEY=sb_secret_xxxxx
SUPABASE_STORAGE_BUCKET=site-presentation
MEDIA_STORAGE_BACKEND=supabase
```

Préparer ou mettre à jour le bucket :

```powershell
python scripts/setup_supabase_storage.py
```

Le bucket est public en lecture pour afficher les images. Les écritures passent uniquement par l’endpoint admin FastAPI et la clé serveur.

## Validation

```powershell
python scripts/test_supabase_connection.py --auth-smoke
```

Résultat attendu :

- `SELECT 1` réussi ;
- tables principales présentes ;
- `/health/ready` retourne PostgreSQL ;
- inscription puis connexion réussies ;
- compte de test supprimé automatiquement.

Après une migration, contrôler aussi les Security Advisors Supabase. Le déploiement ne doit pas être annoncé comme fonctionnel tant que ces contrôles et le smoke test ne sont pas verts.
