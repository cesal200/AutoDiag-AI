# Spec Delta

## ADDED Requirements

### Requirement: Order Chat Authorization by Role
The system SHALL allow order owners and their currently assigned mechanics to send chat messages, while administrators and advisors may inspect but not send messages.

#### Scenario: Administrator or advisor reviews messages
- **WHEN** an administrator or advisor opens an order detail
- **THEN** the system shows its chat history without a message composer

#### Scenario: Administrator attempts to send a chat message
- **WHEN** an administrator or advisor submits a chat message
- **THEN** the system rejects the message and creates no chat record

#### Scenario: Unassigned mechanic attempts to send a message
- **WHEN** a mechanic submits a message for an order assigned to someone else or with no mechanic assigned
- **THEN** the system rejects the message and creates no chat record
