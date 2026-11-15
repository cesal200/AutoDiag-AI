# Spec Delta

## Purpose

Report distribution capability generating PDF workshop reports and delivering them via Telegram Bot API and SMTP email.

## ADDED Requirements

### Requirement: PDF Report Template Rendering
The system SHALL render HTML templates using xhtml2pdf library to generate PDF documents containing order data, vehicle information, symptom analysis, and evidence.

#### Scenario: Template rendering completion
- **WHEN** user requests PDF generation for completed order
- **THEN** system renders templates and produces PDF with all required sections (order details, vehicle, symptoms, budget, evidence)

### Requirement: PDF Generation Time Constraint
The system SHALL generate complete PDF reports in under 30 seconds from request to delivery.

#### Scenario: Fast PDF generation
- **WHEN** PDF generation is initiated
- **THEN** system completes rendering and is ready for delivery within 30 seconds

### Requirement: Telegram Bot API Integration
The system SHALL integrate with Telegram Bot API to send PDF documents to configured chats with order summary caption.

#### Scenario: Telegram report delivery
- **WHEN** PDF is ready for Telegram distribution
- **THEN** system sends document via bot API with caption containing order code and client summary

### Requirement: SMTP Email Integration
The system SHALL integrate with SMTP email server to send PDF reports as attachments with order summary in email body.

#### Scenario: Email report delivery
- **WHEN** PDF is ready for email distribution
- **THEN** system sends email with PDF attachment, subject containing order code, and body with order details

### Requirement: Distribution Method Selection
The system SHALL allow selection of distribution method(s) per order: Telegram, Email, both, or neither.

#### Scenario: Distribution method configuration
- **WHEN** user configures order distribution preferences
- **THEN** system stores preferred method(s) and applies them when report is generated
