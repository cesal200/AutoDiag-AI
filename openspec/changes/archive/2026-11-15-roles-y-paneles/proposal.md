# Proposal

## Why

The current Django project only exposes the built-in Django admin and a single workshop interface backed by hardcoded demo data. There is no login, no role model, and no separation between administrators, clients, and technicians, so each order cannot be scoped to the people allowed to see or operate it. Walk-in clients who arrive at the workshop without a web account also lack a way to receive an order and a tracking link.

## What Changes

- Introduce role-based access with a `PerfilUsuario` linked to Django's `User`: `ADMIN`, `ASESOR`, `MECANICO`, and `CLIENTE`.
- Add login, logout, and client self-registration; technicians and advisors are created by an administrator.
- Add role-specific panels: operational metrics for admin/advisor, own orders for clients, and assigned orders for technicians.
- Enforce role and object-level permissions on order listing, creation, detail, status changes, mechanic assignment, budget approval, and PDF generation.
- Persist orders in the database (migrations included) and generate real order codes (`ORD-YYYY-NNN`) and public tracking tokens.
- Support walk-in orders: an admin/advisor can create an order for an existing client, create a quick client account on the spot, or register only a client name and phone. Every order gets a shareable `seguimiento/<token>/` link.
- Add a public, read-only tracking portal that validates token expiry.
- Fix `EvidenciaSintoma.nivel_riesgo` choices and validate allowed order status transitions.
- Add a `seed_demo` command and automated tests for roles, permissions, walk-in orders, and tracking tokens.

## Capabilities

### New Capabilities

- `role-based-access`: authentication, role assignment, role-specific panels, and object-level authorization for workshop orders.
- `walk-in-orders`: creating orders for clients without an account, quick client creation, and public token-based order tracking.

### Modified Capabilities

- None. The existing `srs-mechanical-workshop` change remains a separate proposal and is not modified here.

## Impact

- **Code**: new `accounts` app; changes to `workshop` models, forms, views, URLs, and admin; new templates and a management command.
- **Database**: initial migrations for `accounts` and `workshop`; new `PerfilUsuario` table and new fields on `OrdenFalla`.
- **Authentication**: Django auth views, login/registration templates, role decorators, and settings redirects.
- **Out of scope**: real multi-tenant `Taller`/`Vehiculo` models, real AI processing, Telegram/SMTP delivery, and full PDF generation. Legacy apps (`reportes`, `reports`, `ai_diagnosis`) are untouched.
