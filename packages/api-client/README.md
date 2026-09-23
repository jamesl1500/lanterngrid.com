# @lanterngrid/api-client

Typed TypeScript client for the Lantern Grid API.

`openapi.json` and `src/schema.d.ts` are generated. Never edit them by hand. After changing
an API route or schema, run from the repo root:

```sh
pnpm gen:api
```

CI regenerates both files and fails if they differ from what is committed.
