# role-based-access Specification

## Purpose

Defines authentication, role assignment, role-specific panels, and object-level authorization so administrators, advisors, clients, and technicians only see and operate the orders their role allows.

## Requirements

### Requirement: Role Assignment
The system SHALL assign every authenticated user exactly one role from ADMIN, ASESOR, MECANICO, or CLIENTE through a profile linked one-to-one with the user account.

#### Scenario: New registration becomes a client
- **WHEN** a visitor completes public registration
- **THEN** the system creates the user with the CLIENTE role and marks the account as authenticated

#### Scenario: Existing superuser becomes an administrator
- **WHEN** an existing superuser has no role profile
- **THEN** the system assigns the ADMIN role to that account

### Requirement: Authentication Required
The system SHALL require an authenticated session to access panels and workshop operations, redirecting anonymous visitors to the login page.

#### Scenario: Anonymous access to a panel
- **WHEN** an anonymous visitor requests a role panel
- **THEN** the system redirects to the login page and returns to the requested panel after successful authentication

### Requirement: Client Self-Registration
The system SHALL allow public registration only for the CLIENTE role and SHALL ignore any role value supplied by the registrant.

#### Scenario: Registrant attempts to choose a privileged role
- **WHEN** a registrant submits a role of ADMIN, ASESOR, or MECANICO during registration
- **THEN** the system creates the account with the CLIENTE role

### Requirement: Role Panel Routing
The system SHALL route each authenticated user from the general panel to the panel for their role and SHALL deny access to panels belonging to another role.

#### Scenario: Client opens the admin panel
- **WHEN** a user with the CLIENTE role requests the administrator panel
- **THEN** the system responds with HTTP 403 and does not expose operational data

#### Scenario: Technician opens the technician panel
- **WHEN** a user with the MECANICO role requests the technician panel
- **THEN** the system shows only orders assigned to that technician

### Requirement: Order Visibility by Role
The system SHALL filter order listings by role: clients see only their own orders, technicians see only orders assigned to them, and administrators and advisors see all orders.

#### Scenario: Client order list isolation
- **WHEN** a client opens the order list
- **THEN** the system returns only orders whose client is that authenticated user

#### Scenario: Technician order list isolation
- **WHEN** a technician opens the order list
- **THEN** the system returns only orders whose assigned mechanic is that authenticated user

### Requirement: Order Creation Authorization
The system SHALL allow clients to create orders for themselves and administrators or advisors to create orders for any client or walk-in client, and SHALL deny order creation to technicians.

#### Scenario: Client creates an order
- **WHEN** an authenticated client submits a valid order form
- **THEN** the system creates the order linked to that client with status PRE_DIAGNOSTICO

#### Scenario: Technician attempts to create an order
- **WHEN** a technician submits an order creation request
- **THEN** the system responds with HTTP 403 and creates no order

### Requirement: Order Detail Authorization
The system SHALL allow access to an order detail or its PDF only to the owning client, the assigned technician, or an administrator or advisor.

#### Scenario: Client opens another client's order
- **WHEN** a client requests the detail of an order owned by a different client
- **THEN** the system responds with HTTP 403 and does not reveal order data

### Requirement: Status Transition Authorization
The system SHALL allow only the assigned technician, an administrator, or an advisor to change order status and SHALL reject transitions that do not follow the defined workflow.

#### Scenario: Invalid status transition
- **WHEN** an authorized user requests a transition not allowed from the current status
- **THEN** the system rejects the change and keeps the previous status

### Requirement: Mechanic Assignment Authorization
The system SHALL allow only administrators and advisors to assign or reassign a mechanic to an order.

#### Scenario: Technician attempts to reassign an order
- **WHEN** a technician submits a mechanic assignment request
- **THEN** the system responds with HTTP 403 and keeps the current mechanic

### Requirement: Budget Approval Authorization
The system SHALL allow only the client who owns an order to approve its budget items.

#### Scenario: Client approves a budget item
- **WHEN** the owning client submits an approval for a budget item
- **THEN** the system marks that item as approved

#### Scenario: Technician attempts to approve a budget item
- **WHEN** a technician submits an approval for a budget item
- **THEN** the system responds with HTTP 403 and leaves the item unapproved

### Requirement: Administrator Panel Access
The system SHALL grant the operational administrator panel to ADMIN and ASESOR roles and SHALL restrict Django admin access to staff accounts.

#### Scenario: Advisor opens the operational panel
- **WHEN** an advisor requests the administrator panel
- **THEN** the system shows workshop metrics and recent orders without requiring staff status

#### Scenario: Client requests Django admin
- **WHEN** a client requests the Django admin URL
- **THEN** the system redirects to the admin login and denies access
