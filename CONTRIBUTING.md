# Contributing to netizen

Thanks for helping improve netizen.

## What This Repo Is

netizen hosts community OpenAPI specs and lightweight Swagger UI pages for useful services.

Goals:

- Keep specs easy to consume.
- Keep maintenance low.
- Keep outputs publicly reusable.

## Before You Open a PR

1. Make sure your change is service-focused and useful to end users.
2. Keep changes small and scoped.
3. Prefer updating existing patterns over inventing new structure.

## Spec Folder Conventions

Each service folder should contain exactly:

1. `index.html`
2. `*-api_openapi-vX.Y.Z.json`

Examples:

- `technitium-dns/index.html`
- `technitium-dns/technitium-dns-api_openapi-v3.0.3.json`

## Catalog Requirements

Every service folder must have a matching entry in `catalog.json` with populated fields.

Required fields:

- `name`
- `description`
- `tags`
- `endpoints`
- `site`

## Workflow Behavior

On build runs, CI will:

1. Validate folder structure.
2. Validate `catalog.json` completeness.
3. Generate ZIP bundles for all catalog folders.
4. Publish/update release ZIP assets on `main`.

If CI fails, check workflow output in `.github/workflows/spec-structure.yml`.

## Adding a New Service

1. Create the folder with `index.html` and OpenAPI JSON.
2. Add a `catalog.json` entry keyed by folder name.
3. Keep copy focused on the service value, not spec construction details.
4. Open a PR.

## License

Contributing means your code/content is accepted under this repo's license model:

- Code: `0BSD` (`LICENSE`)
- Non-code/spec content: `CC0 1.0` (`LICENSE-CONTENT`)
