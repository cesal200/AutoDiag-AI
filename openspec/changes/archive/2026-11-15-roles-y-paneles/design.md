# Design

## Context

See `proposal.md` for motivation and the two delta specs for required behavior. The project is a Django 6.1 application with a `workshop` app whose views currently return hardcoded data, no migrations for its models, and no authentication beyond the built-in Django admin. The `User` model is Django's default, and `OrdenFalla.mecanico_asignado` already references it. The database is SQLite and the existing `db.sqlite3` contains only Django's auth/admin tables.

Constraints:
- Keep the default `User` model to avoid resetting the existing database.
- Stay within the minimal functional scope: no real multi-tenancy, AI, Telegram, SMTP, or PDF engine.
- Preserve the existing `workshop` URL names where practical (`orden_nueva`, `orden_lista`, `orden_detalle`, `generar_pdf`).

## Goals / Non-Goals

**Goals:**
- Add a role profile and authorization layer that is easy to extend.
- Replace demo data with persisted orders and real role-scoped querysets.
- Support walk-in orders and quick client creation without weakening order ownership rules.
- Generate a public tracking token for every order and expose a read-only portal.

**Non-Goals:**
- A custom `AUTH_USER_MODEL`.
- Tenant isolation through a `Taller` foreign key.
- Password-invite emails or a full client onboarding flow.
- Real AI/PDF/Telegram/SMTP integrations.

## Decisions

### Role model: `PerfilUsuario` OneToOne instead of a custom user
- **Choice**: New `accounts` app with `PerfilUsuario(user, rol, telefono, especialidad, taller)`, auto-created by a `post_save` signal and backfilled by a data migration.
- **Rationale**: The default `User` is already referenced by `OrdenFalla` and the admin; a profile avoids destructive migration work. It also mirrors the architecture document's `PerfilUsuario` and leaves room for the future `Taller` FK.
- **Alternatives**: Custom user model (cleaner long term but requires database reset); Django Groups (native permissions but poor fit for a client role with owned orders).

### Roles and privilege mapping
- `ADMIN`: full operational access plus Django admin when `is_staff`.
- `ASESOR`: same operational access as ADMIN, no Django admin.
- `MECANICO`: assigned orders only; status and budget edits; no assignment.
- `CLIENTE`: own orders only; creation, budget approval, tracking link.
- Superusers are treated as ADMIN even if their profile is missing.

### Authorization: decorators plus object-level checks
- **Choice**: `rol_requerido(*roles)` decorator and a CBV mixin in `accounts/decorators.py`; detail-level views perform explicit ownership checks and raise `PermissionDenied`.
- **Rationale**: Decorators keep URL wiring readable; object checks prevent IDOR on detail/PDF views. Wrong role returns HTTP 403 rather than silently redirecting, which makes tests deterministic.
- **Alternatives**: Django permissions/groups (more configuration for little benefit here); middleware (hidden control flow).

### Order ownership with nullable client and walk-in fields
- **Choice**: Keep `cliente` nullable, add `nombre_cliente_walkin` and `telefono_cliente_walkin`, and validate that at least one identification exists. Add a `cliente_efectivo` property for display.
- **Rationale**: A client may arrive in person or via WhatsApp with no account. The token portal remains the delivery mechanism; the admin can optionally create an account.
- **Alternatives**: Requiring an account before creating an order (blocks walk-ins); a separate `Cliente` model (out of scope and would need vehicle relations).

### Quick client creation
- **Choice**: A dedicated form/view available to ADMIN/ASESOR that creates a `User` with the email as username, `set_unusable_password()`, and a CLIENTE profile; duplicate emails are rejected.
- **Rationale**: Covers the "create the account on the spot" case without building an invitation flow.
- **Alternatives**: Inline user creation inside the order form (more coupling and validation complexity); sending an invite email (no email backend configured for real delivery).

### Order code and token generation
- **Choice**: Generate `ORD-YYYY-NNN` inside `transaction.atomic()` using the latest order for the year with `select_for_update()`, retrying on conflict. Generate `uuid4()` token and a 30-day expiry on every save when missing.
- **Rationale**: The current model default is a static string and would violate uniqueness on the second order. Tokens must exist for walk-ins too.
- **Alternatives**: Database sequence (SQLite limitations), UUID-only codes (less human-readable).

### Status transitions
- **Choice**: Central transition map in `OrdenFalla.puede_transicionar_a()` and a POST-only view that validates it.
- **Rationale**: One source of truth for the workflow, usable by views, tests, and future services.
- **Alternatives**: Form-level validation only (bypassable by other callers).

### Public tracking
- **Choice**: `GET /seguimiento/<uuid:token>/`, lookup by token, reject expired tokens with 404, render a read-only template.
- **Rationale**: Simple, no session required, no sensitive client data exposed.
- **Alternatives**: Signed URLs (more complex, no additional benefit for this scope).

### Templates and navigation
- Keep the existing visual language in `base.html`; make navigation conditional on role and add login/registration links for anonymous users.
- Add `dashboard/admin.html`, `dashboard/cliente.html`, `dashboard/tecnico.html`, `workshop/seguimiento_publico.html`, `registration/login.html`, and `accounts/registro.html`.

## Risks / Trade-offs

- [Risk] Existing `db.sqlite3` has no `workshop` tables → Mitigation: create initial migrations and run `migrate`; verify with `manage.py check` before seeding.
- [Risk] Users created before the profile signal lack a profile → Mitigation: data migration backfill plus a `get_or_create` helper used by decorators and templates.
- [Risk] Walk-in orders without accounts have no login-based access → Mitigation: always issue a tracking token; admin can regenerate it.
- [Risk] Race conditions when generating sequential order codes → Mitigation: atomic transaction, row lock, and retry on `IntegrityError`.
- [Risk] Quick-client accounts have no usable password → Mitigation: admin can share the tracking link; password reset/invite flow is explicitly out of scope.
- [Risk] ASESOR gets operational admin powers but no Django admin → Mitigation: document the distinction in the panel and tests.

## Migration Plan

1. Create the `accounts` app and its initial migration.
2. Add workshop model fields and create the initial `workshop` migration.
3. Backfill profiles for existing users (superusers → ADMIN, staff → ASESOR, others → CLIENTE).
4. Run `migrate`, then `seed_demo` for local verification.
5. Rollback: migrations are additive; dropping the new tables/fields is safe in development. No existing workshop data exists to migrate.

## Open Questions

None. Decisions that would affect scope were resolved with the user (profile model, client access via login plus token, minimal functional scope, Django admin plus metrics panel).
