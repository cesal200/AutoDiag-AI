# Design

## Context

Django 6.1.3 is currently deployed with WSGI, SQLite, role profiles and order-detail authorization centralized in `accounts.permissions`. The order detail already presents budget, evidence, status and report information. The chat can use the existing authenticated page and form-post patterns.

## Goals / Non-Goals

**Goals:**
- Persist messages in the database and associate them with an order and author.
- Let the owning client and assigned mechanic read and send messages; keep operational roles read-only.
- Render the chat in the existing order detail template.
- Keep a chronological history available when the page is reopened.

**Non-Goals:**
- Real-time delivery, WebSockets, online presence or read receipts.
- File or image chat attachments.
- Push notifications outside the application.
- Cross-workshop chat or direct messages unrelated to an order.
- Chat access through public tracking links.

## Decisions

- **Use the existing Django request/response flow:** Submit messages through a CSRF-protected POST form and render the updated order detail after saving. This avoids introducing a real-time service for a simple order conversation.
- **Persist only essential message data:** Store order, author, message text and creation timestamp. Sort by creation time; omit read status, delivery status and presence.
- **Reuse existing order authorization:** Permit sending only for the owning client or assigned mechanic. Administrators and advisors may see the history in read-only mode. Public tracking remains separate and does not include messages.
- **Avoid new dependencies:** Keep the existing WSGI, database and template setup; no Channels, Redis or browser socket code is needed.

## Risks / Trade-offs

- [Messages do not appear until the page reloads] → Redirect back to the order detail after a successful send and render the newly saved message in the response.
- [Order reassignment changes who may participate] → Check the current order owner and mechanic assignment on every message submission.
- [Long or empty messages reduce usability] → Validate non-empty text and impose a practical maximum length in the form and model.

## Migration Plan

1. Add the chat message model and migration.
2. Add the message form and authenticated POST view with order authorization.
3. Add the history and form to the order-detail template.
4. Add focused model, form and permission tests.
5. Run migrations, Django checks and the focused workshop test suite.

Rollback removes the chat form and view; the message migration can be reversed separately if no stored conversation needs to be retained. No existing order or public-tracking behavior is changed.
