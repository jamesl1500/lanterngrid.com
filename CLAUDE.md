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
- User-written text is Markdown, rendered on the server by `components/markdown.tsx` (Shiki for
  code, no raw HTML). The API finds #tags and @mentions (`posts/text.py`) and the web only links
  the ones it returns; `slugify` in `lib/tags.ts` must stay in step with `tags/schemas.py`.
- Python: Ruff (lint + format) and mypy strict must pass. TypeScript: ESLint, Prettier and
  strict tsc must pass.
- API tests run against a real Postgres and Redis, not mocks. `tests/conftest.py` points them at
  a separate `<db>_test` database and Redis db 15, and truncates every table after each test
  (seeded `tags` rows are kept). Only outside services (GitHub, file storage) are faked, by
  overriding their FastAPI dependency; see `tests/fakes.py`.
- Uploads never pass through the API: the browser gets a presigned PUT URL from
  `POST /v1/me/uploads`, sends the file to the bucket, then attaches the key. Store object keys
  in the database, not URLs; build URLs with `public_url()`.

## Auth

- FastAPI owns auth. The session cookie `lg_session` holds a random token; only its SHA-256 is
  stored (`sessions` table). Email links (`email_tokens`) work the same way and are single-use.
- Routes get the signed-in person from `CurrentUserDep` / `OptionalUserDep`
  (`app.modules.auth.deps`); social features use `MemberDep`, which also requires a username.
  Writes from another site's `Origin` are rejected in `app/main.py`.
- On the web side, server components use `getMe()` / `requireMe()` from `lib/session.ts`;
  client forms call `browserApi` and wrap calls in `attempt()` from `lib/errors.ts`.
- A signed-in account has no username until onboarding; `requireMe()` sends it there.

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
