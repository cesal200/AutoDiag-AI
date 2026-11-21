# Tasks

## 1. Message Persistence and Validation

- [ ] 1.1 Add a `MensajeChat` model linked to an order and author, with message text and creation timestamp; verify its migration and chronological ordering.
- [ ] 1.2 Add message validation for required text and maximum length; verify empty and overlong messages are rejected.

## 2. Message Submission and Access

- [ ] 2.1 Add a CSRF-protected POST endpoint that saves a message and redirects to its order; verify the saved message appears in the response.
- [ ] 2.2 Restrict sending to the order owner and currently assigned mechanic, and keep administrator/advisor views read-only; verify forbidden users cannot create messages.

## 3. Order Chat Interface

- [ ] 3.1 Add chronological message history and a simple message form to `orden_detalle.html`; verify the client and assigned mechanic can use it.
- [ ] 3.2 Show chat history read-only to administrators/advisors and omit chat from public tracking; verify neither view exposes a send form.

## 4. Verification

- [ ] 4.1 Add model, form and view tests for message persistence, chronological history, ownership, mechanic reassignment and denied access; verify the focused workshop tests pass.
- [ ] 4.2 Run migrations, `manage.py check` and the focused workshop test suite; verify existing order behavior remains intact.
