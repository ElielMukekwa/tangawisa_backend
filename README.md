# Backend Tangawisa

API FastAPI de la marketplace Tangawisa. Le backend conserve l’architecture existante :

- FastAPI pour les routes publiques, client, vendeur, support et administration ;
- SQLAlchemy pour la persistance ;
- JWT Tangawisa pour l’authentification ;
- PostgreSQL Supabase en production ;
- Supabase Storage pour les images administrées ;
- Vercel Functions pour l’exécution du backend.

> Le schéma scolaire MariaDB `ecole_gestion` ne correspond pas aux modèles de ce dépôt. Il ne doit pas être importé dans cette base Tangawisa : cela casserait les routes marketplace existantes.

## Démarrage local

Depuis `backend` :

```powershell
Copy-Item .env.example .env
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Vérifications :

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/ready
Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/info
```

Interfaces locales :

- documentation API : `http://127.0.0.1:8000/docs` ;
- présentation : `http://127.0.0.1:8000/presentation/` ;
- administration HTML : `http://127.0.0.1:8000/admin`.

## Tests

```powershell
python -m compileall -q app scripts tests
python -m unittest discover -s tests -v
```

Test réel Supabase, après configuration de `DATABASE_URL` :

```powershell
python scripts/test_supabase_connection.py --auth-smoke
```

Le compte créé par le smoke test est supprimé automatiquement.

## Production Vercel + Supabase

Le guide complet est dans [DEPLOIEMENT_VERCEL_SUPABASE.md](DEPLOIEMENT_VERCEL_SUPABASE.md).

Points obligatoires :

- définir la racine Vercel sur `backend` ;
- utiliser le pooler transactionnel Supabase, port `6543` ;
- définir un `JWT_SECRET_KEY` aléatoire d’au moins 32 caractères ;
- garder `BOOTSTRAP_DATABASE=false` et `SEED_DEVELOPMENT_DATA=false` ;
- utiliser `MEDIA_STORAGE_BACKEND=supabase` ;
- ne jamais committer `DATABASE_URL`, `SUPABASE_SECRET_KEY` ou `JWT_SECRET_KEY`.

La production refuse volontairement de démarrer avec SQLite ou une clé JWT d’exemple. Cela évite un déploiement apparemment sain mais non persistant.
