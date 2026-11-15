# Spec Delta

## Purpose

Workshop management capability covering the complete repair order lifecycle with AI pre-diagnosis integration for mechanical centers.

## ADDED Requirements

### Requirement: Order Creation
The system SHALL allow creation of a repair order with complete vehicle data (plate, brand, model, year, engine, mileage) and client narrative.

#### Scenario: Successful order creation
- **WHEN** user completes the order form with valid vehicle data
- **THEN** system generates order code OR-YYYY-NNN and assigns status PRE_DIAGNOSTICO

### Requirement: Symptom Registration
The system SHALL allow registration of symptoms through multiple modalities: voice transcription, photo capture, and textual narrative.

#### Scenario: Voice symptom capture
- **WHEN** user records audio describing the vehicle symptom
- **THEN** system transcribes audio and returns normalized symptom description

### Requirement: AI Pre-Diagnosis
The system SHALL provide at least three probable causes ordered by probability for each reported symptom, along with risk level classification.

#### Scenario: AI analysis completion
- **WHEN** multimodal AI processes vehicle data, images, and narrative
- **THEN** system returns sintomas_normalizados, causas_probables (max 3), nivel_riesgo, and pruebas_taller_sugeridas

### Requirement: Order Status Workflow
The system SHALL enforce valid status transitions: PRE_DIAGNOSTICO → EN_TALLER → ESPERA_REPUESTO → LISTO → ENTREGADO.

#### Scenario: Status transition validation
- **WHEN** user attempts to transition order status
- **THEN** system validates transition is allowed and updates timestamp

### Requirement: Budget Management
The system SHALL allow addition of items (parts and labor) to order budget with unit price, quantity, and client approval.

#### Scenario: Budget item approval
- **WHEN** mechanic adds item to budget
- **THEN** system records item type (REPUESTO/MANO_OBRA), description, quantity, price, and approval flag

### Requirement: PDF Report Generation
The system SHALL generate PDF workshop reports using xhtml2pdf rendering of HTML templates with all order data and evidence.

#### Scenario: PDF generation completion
- **WHEN** user requests PDF report for completed order
- **THEN** system renders template and generates downloadable PDF in under 30 seconds
