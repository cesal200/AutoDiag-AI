# Spec Delta

## ADDED Requirements

### Requirement: Order Detail Chat Section
The system SHALL present a simple order-specific message history and form in the authenticated order detail view.

#### Scenario: Client or assigned mechanic views the order
- **WHEN** the owner or currently assigned mechanic opens the order detail
- **THEN** the system shows the conversation and a form for sending a message

#### Scenario: Admin or advisor reviews the order
- **WHEN** an authenticated administrator or advisor opens an order detail
- **THEN** the system shows the conversation without a message form

#### Scenario: Message is submitted
- **WHEN** an authorized participant submits a non-empty message
- **THEN** the system saves it and displays it in the order conversation
