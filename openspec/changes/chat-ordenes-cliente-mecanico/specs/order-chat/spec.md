# Spec Delta

## Purpose

Permite al cliente propietario y al mecánico asignado intercambiar mensajes persistentes desde el detalle de una orden.

## ADDED Requirements

### Requirement: Order Chat Message Persistence
The system SHALL persist each non-empty chat message with its order, author, text, and creation timestamp.

#### Scenario: Authorized participant sends a message
- **WHEN** the owning client or assigned mechanic submits a valid message from the order detail
- **THEN** the system stores the message for that order and shows it in the conversation

#### Scenario: Empty message submission
- **WHEN** a participant submits whitespace-only text
- **THEN** the system rejects the message and does not create a chat record

### Requirement: Order Chat History
The system SHALL display an order's saved messages in chronological order in its authenticated detail page.

#### Scenario: Authorized participant opens an order
- **WHEN** the owning client or assigned mechanic opens the order detail
- **THEN** the system shows the order's messages with author and timestamp

#### Scenario: Participant returns to the order
- **WHEN** an authorized participant reloads or revisits the order detail
- **THEN** the system continues to show the saved conversation

### Requirement: Order Chat Authorization
The system SHALL allow only the owning client and the currently assigned mechanic to send messages in an order conversation.

#### Scenario: Owning client sends a message
- **WHEN** the authenticated owner submits a message for their order
- **THEN** the system accepts it even if no mechanic is assigned

#### Scenario: Assigned mechanic sends a message
- **WHEN** the authenticated mechanic assigned to the order submits a message
- **THEN** the system accepts and associates the message with that mechanic

#### Scenario: Unauthorized user requests chat access
- **WHEN** another client, a technician without assignment, or an anonymous visitor attempts to read or send messages
- **THEN** the system denies access and does not expose the conversation

### Requirement: Public Tracking Chat Isolation
The system SHALL keep public tracking links read-only and SHALL NOT provide chat access through them.

#### Scenario: Visitor opens a public tracking link
- **WHEN** a visitor requests public order tracking
- **THEN** the system shows tracking information without messages or chat controls
