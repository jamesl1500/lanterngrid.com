# Lantern Grid

The social network for software engineers. Share updates, code snippets, repos and wins, make
friends and message them in real time.

## Stack

| Layer    | Tech                                                                      |
| -------- | ------------------------------------------------------------------------- |
| Web      | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4            |
| API      | FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, Python 3.13          |
| Data     | PostgreSQL 18, Redis 7, S3-compatible storage (MinIO locally, R2 in prod) |
| Monorepo | pnpm workspaces + Turborepo, uv workspace for Python                      |

## Repo layout

```
apps/
  web/          Next.js app
  api/          FastAPI service (app/modules/<feature>/ holds router, schemas, models, service)
packages/
  ui/           Design tokens and shared React components
  api-client/   TypeScript client generated from the API's OpenAPI schema
  config/       Shared tsconfig presets
infra/
  docker-compose.yml   Postgres, Redis, MinIO, Mailpit for local dev
  docker/              Production Dockerfiles
```

## Getting started

Prerequisites: Node 22+, pnpm 10, [uv](https://docs.astral.sh/uv/), Docker.

```sh
cp .env.example .env
pnpm install
uv sync
pnpm services:up      # Postgres, Redis, MinIO, Mailpit
pnpm db:migrate
pnpm dev              # web on :3000, API on :8000
```

Open http://localhost:3000 and create an account. Verification and password-reset emails
land in Mailpit at http://localhost:8025. To try GitHub sign-in, create a GitHub OAuth app with
the callback URL `http://localhost:3000/api/v1/auth/github/callback` and put its client id and
secret in `.env`.

Avatars and banners upload straight from the browser to MinIO (console at
http://localhost:9001, user and password `lanterngrid`); `pnpm services:up` creates the
`lanterngrid-media` bucket.

The system status panel on the home page shows whether the API,
Postgres and Redis are reachable. The UI kit lives at http://localhost:3000/kit and the API
docs at http://localhost:8000/docs.

## Everyday commands

| Command          | What it does                                                   |
| ---------------- | -------------------------------------------------------------- |
| `pnpm dev`       | Run web and API with hot reload                                |
| `pnpm lint`      | ESLint for TypeScript, Ruff for Python                         |
| `pnpm typecheck` | tsc for TypeScript, mypy for Python                            |
| `pnpm test`      | Vitest for TypeScript, pytest for Python (needs services up)   |
| `pnpm gen:api`   | Regenerate the TypeScript API client after changing API routes |
| `pnpm format`    | Prettier and Ruff format                                       |

New migration: `cd apps/api && uv run alembic revision --autogenerate -m "add users"`.

## Deployment

- **Web** deploys to Vercel with `apps/web` as the root directory. Set `API_URL` to the API's
  public URL.
- **API** deploys to Railway from `infra/docker/api.Dockerfile` (build context is the repo root).
  Set `DATABASE_URL` (use the `postgresql+asyncpg://` scheme), `REDIS_URL`, `CORS_ORIGINS`,
  `WEB_URL`, `ENVIRONMENT`, the `SMTP_*` and `EMAIL_*` settings, and the GitHub OAuth app's
  `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` (callback URL
  `https://<web domain>/api/v1/auth/github/callback`). Use `alembic upgrade head` as the
  pre-deploy command.
- **Uploads** go to a Cloudflare R2 bucket. Turn on public access (r2.dev or a custom domain),
  create an R2 API token with object read and write on the bucket, and set the `STORAGE_*`
  variables on the API (see `.env.example`). Browsers upload with presigned PUTs, so the bucket
  needs this CORS policy:

  ```json
  [
    {
      "AllowedOrigins": ["https://<web domain>"],
      "AllowedMethods": ["PUT"],
      "AllowedHeaders": ["Content-Type"],
      "MaxAgeSeconds": 3600
    }
  ]
  ```
