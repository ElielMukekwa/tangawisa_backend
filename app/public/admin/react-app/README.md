# Tangawisa Site Admin React

Conversion React du back-office du site de presentation.

## Installation

```bash
cd backend/app/public/admin/react-app
npm install
```

## Developpement

```bash
npm run dev
```

## Build

```bash
npm run build
```

La SPA React consomme les endpoints backend existants:

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/site-presentation/admin/summary`
- `GET /api/v1/site-presentation/admin/content`
- `PUT /api/v1/site-presentation/admin/content`
- `GET /api/v1/site-presentation/admin/media`
- `POST /api/v1/site-presentation/admin/upload-image`
