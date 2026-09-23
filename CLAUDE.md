# Lantern Grid

Social network for software engineers. Monorepo: Next.js web app + FastAPI API + Postgres.
See README.md for setup and commands.

## Layout

- `apps/web` Next.js 16 App Router. Server components by default; `'use client'` only for
  interactivity. `@/` aliases the app root.
- `apps/api` FastAPI. One folder per feature in `app/modules/<feature>/` with `router.py`,
  `schemas.py` (Pydantic), `models.py` (SQLAlchemy) and `service.py` (business logic). Routers
  are mounted under `/v1` in `app/main.py`.
- `packages/ui` design tokens (`src/styles.css`) and shared components. TypeScript source,
  compiled by Next via `transpilePackages`.
- `packages/api-client` generated client. Never edit `openapi.json` or `src/schema.d.ts` by
  hand; run `pnpm gen:api` after any API route or schema change and commit the result. CI fails
  if they drift.

## Conventions

- Browser code calls the API through `/api/*` (Next rewrite to FastAPI, same origin). Server
  code uses `serverApi()` from `apps/web/lib/api.ts`.
- Give every FastAPI route an explicit `operation_id` and a Pydantic response model; the
  TypeScript client is typed from them.
- Use `SessionDep` from `app.core.db` for DB access in routes. Migrations are Alembic, one per
  change, reviewed like code. Autogenerate, then read and fix the result.
- Primary keys will be UUIDv7 so lists page with `where id < :cursor order by id desc`, never
  OFFSET.
- Python: Ruff (lint + format) and mypy strict must pass. TypeScript: ESLint, Prettier and
  strict tsc must pass.
- API tests run against a real Postgres and Redis, not mocks.

## Design rules

The look is flat, sharp and colorful. Use tokens from `packages/ui/src/styles.css` through
Tailwind classes (`bg-surface`, `text-ink-2`, `border-line-strong`, `shadow-hard`, ...).

- No rounded corners. The `rounded-*` scale is removed on purpose; don't add radii back.
- Hairline `border-line` for structure, 2px `border-line-strong` for interactive or raised
  things. Shadows are hard offsets (`shadow-hard*`) with no blur, used sparingly.
- Each content kind has one accent: update=cyan, snippet=violet, repo=lime,
  achievement=amber, message=magenta, alert=coral (`kindAccent` in `packages/ui`).
- Fonts: Chakra Petch (display, headings), IBM Plex Sans (body), JetBrains Mono (code,
  handles, labels).
- Dark theme is the default (`data-theme="dark"` on `<html>`); every token has a light value
  too, so never hardcode colors that only work in one theme.
- New shared components go in `packages/ui` and get added to the `/kit` page.
