# walk-in-orders Specification

## Purpose

Enables administrators and advisors to open orders for clients who have no web account, either with only contact data or with a quick account, while giving every client a public token-based tracking link.

## Requirements

### Requirement: Walk-in Order Creation
The system SHALL allow an administrator or advisor to create an order without selecting a registered client when a walk-in client name is provided, and SHALL reject orders that have neither a linked client nor a walk-in name.

#### Scenario: Walk-in order with contact data only
- **WHEN** an administrator submits an order with a walk-in name and phone and no linked client
- **THEN** the system creates the order with an empty client reference and stores the walk-in name and phone

#### Scenario: Order without client identification
- **WHEN** an administrator submits an order with neither a linked client nor a walk-in name
- **THEN** the system rejects the order with a validation error

### Requirement: Quick Client Creation
The system SHALL allow an administrator or advisor to create a client account while creating an order, assigning the CLIENTE role and requiring the client to obtain credentials before first login.

#### Scenario: Quick client account creation
- **WHEN** an administrator submits a quick client form with name, email, and phone during order creation
- **THEN** the system creates a user with the CLIENTE role, links the order to that user, and sets a non-usable password

#### Scenario: Duplicate quick client email
- **WHEN** an administrator submits a quick client form with an email already used by another account
- **THEN** the system rejects the creation with a validation error and creates no duplicate account

### Requirement: Automatic Tracking Token
The system SHALL generate a unique public tracking token and an expiry timestamp for every created order, including walk-in orders.

#### Scenario: Token generated on creation
- **WHEN** any order is created
- **THEN** the system stores a unique token and a future expiry timestamp for that order

### Requirement: Public Tracking Portal
The system SHALL expose a read-only tracking page for a valid, unexpired token showing the order status, vehicle, and budget summary without requiring authentication.

#### Scenario: Valid tracking link
- **WHEN** a visitor opens a tracking link with a valid unexpired token
- **THEN** the system displays the order status, vehicle, and budget summary without exposing client credentials

#### Scenario: Expired or unknown tracking link
- **WHEN** a visitor opens a tracking link whose token is expired or unknown
- **THEN** the system responds with HTTP 404

### Requirement: Tracking Token Regeneration
The system SHALL allow administrators and advisors to regenerate an order's tracking token and expiry, invalidating the previous link.

#### Scenario: Regenerate an expired link
- **WHEN** an administrator regenerates the token for an order
- **THEN** the system issues a new token and expiry and the previous token no longer resolves
