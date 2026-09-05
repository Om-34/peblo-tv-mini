# Peblo TV Mini

A small full-stack implementation of the Peblo TV Mini take-home: an internal CMS feeds a FastAPI/PostgreSQL content model, an atomic publish step produces a pre-published catalogue, and a separate React viewer consumes only that catalogue.

## Run

Requirements: Docker + Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000/docs
- CMS: http://localhost:5173
- Viewer: http://localhost:5174
- Health: http://localhost:8000/health

Demo accounts: `admin / admin123`, `editor / editor123`.

The API container runs Alembic migrations and then the seed process. The seed intentionally preserves invalid challenge data so the validation report can surface it.

## Architecture

`CMS -> FastAPI -> PostgreSQL -> publish service -> versioned catalogue -> Viewer`.

The viewer never calls admin resources. It reads `/catalog` and `/catalog/search` only.

## Important challenge decisions

- **Season 0:** stored as a trailer season but emitted as `trailers`, not a normal viewer season.
- **content_group:** language variants sharing a group collapse to one episode with a sorted `languages` list.
- **Artwork:** backend checks MIME/image validity, 200 KB ceiling, exact target dimensions and aspect ratio. The exact target dimensions are used because the supplied reference gives concrete target pixels and the exercise asks for genuine enforcement.
- **Invalid seed data:** the seed contains a missing-artwork published episode, a duplicate `(content_group, language)` pair, draft content, and a show with no section. The last item is not a publish blocker while that show remains draft; it becomes a blocker if the show is published.

## Atomic publishing

Publishing creates a complete content-addressed catalogue under `storage/catalogues/catalogue-<sha256>.json`, then atomically replaces a small `current.json` pointer using `os.replace`. Readers resolve the pointer and only then open the completed immutable file. A crash before the pointer switch therefore leaves the previous valid catalogue active; a failed publish never overwrites the live file. Re-publishing identical data produces the same hash and is naturally idempotent at the catalogue level.

## Storage abstraction

Application code uses the `Storage` class for media and catalogue writes. In production I would add an `R2Storage` implementation using the same methods and select it from configuration. The catalogue publication contract would remain unchanged; only object put/read and atomic activation semantics would be adapted to object storage (for example, immutable versioned objects plus an atomically updated manifest/pointer).

## Search and scale

Search is server-side over the already-published catalogue, with composed `q`, category, language and section filters. For this deliberately small catalogue that keeps the viewer path simple and avoids a database dependency. It stops being a good approach when catalogue size makes each request's JSON scan materially expensive or latency-sensitive; next I would add an indexed search projection/full-text PostgreSQL search, or a dedicated search service if scale justified it.

## Why pre-publish a catalogue?

The viewer is a read-heavy surface. A pre-published file makes reads cheap, deterministic and independent of CMS/database availability, while publication is the controlled point where validation and content grouping happen. The trade-off is freshness: database edits do not reach viewers until a successful publish. It also means the catalogue schema must be treated as a versioned public contract.

## CI / secrets / alerting

GitHub Actions runs lint, tests and image builds. The deploy job is represented as a documented placeholder; production would push immutable images to a registry and update the service in the target environment.

`.env.example` documents runtime configuration. In production, secrets should come from the deployment platform's secret manager (or Vault/KMS-backed equivalent), never from Git. Rotate database credentials and signing keys independently.

A useful alert is repeated catalogue publish failure. Publishing is the boundary between editable CMS state and viewer state, so repeated failures mean viewer content can become stale even though editors believe changes are ready.

## Testing

Risk-focused tests cover catalogue language grouping and reference constraints. The Docker workflow is the primary integration path; additional API/integration tests can be expanded if more time remains.

## What I left out

The optional rollback, publish dry-run diff and audit log are intentionally not included. The 6–8 hour exercise rewards reliable core behavior, so the implementation prioritizes validation, atomic publishing, RBAC, usable CMS flow, viewer separation and reproducible Docker startup.

## AI disclosure

AI assistance was used for implementation brainstorming, code review and debugging. Suggestions were treated as drafts: requirements were checked against the supplied challenge/reference files, and generated code was expected to be tested rather than accepted blindly.

## Approximate effort

- Backend/data model: ~2 h
- Validation/artwork/publish: ~2 h
- CMS: ~1 h
- Viewer: ~1 h
- Docker/CI/tests/docs: ~1–2 h
