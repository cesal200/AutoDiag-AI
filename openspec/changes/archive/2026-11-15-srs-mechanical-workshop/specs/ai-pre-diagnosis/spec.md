# Spec Delta

## Purpose

AI pre-diagnosis capability processing multimodal inputs (voice, images, vehicle data) to generate normalized symptoms, probable causes with probabilities, risk levels, and suggested technical tests.

## ADDED Requirements

### Requirement: Multimodal Input Processing
The system SHALL process combined inputs: vehicle data form, client narrative text, attached photographs, and recorded voice notes for each repair order.

#### Scenario: Complete input processing
- **WHEN** user submits vehicle data form, uploads photos, records voice note, and provides narrative
- **THEN** system stores all inputs linked to the repair order and triggers AI analysis

### Requirement: Symptom Normalization
The system SHALL normalize raw symptom descriptions into standardized format using predefined taxonomy for mechanical components and failure modes.

#### Scenario: Symptom normalization output
- **WHEN** AI processes unstructured symptom text
- **THEN** system returns sintomas_normalizados in standardized format with component identifiers

### Requirement: Probable Cause Ranking
The system SHALL order probable causes by descending probability score, providing at least three causes with associated probability percentages for each symptom.

#### Scenario: Cause ranking display
- **WHEN** AI analysis completes
- **THEN** system displays causas_probables array with causa, probabilidad, and ranking position

### Requirement: Risk Level Classification
The system SHALL classify conveyed risk level into exactly one of: PUEDE_RODAR, PRECAUCION, or NO_MOVER_GRUA based on severity assessment.

#### Scenario: Risk level assignment
- **WHEN** AI analyzes symptom severity and vehicle data
- **THEN** system assigns nivel_riesgo from {PUEDE_RODAR, PRECAUCION, NO_MOVER_GRUA} with descriptive rationale

### Requirement: Suggested Technical Tests
The system SHALL suggest specific technical tests or inspections to validate diagnosed causes, including measurement procedures and expected values.

#### Scenario: Test suggestions display
- **WHEN** AI completes cause analysis
- **THEN** system returns pruebas_taller_sugeridas with test description, procedure, and expected values

### Requirement: AI Output JSON Schema
The system SHALL output AI analysis results in JSON format with exact structure: {sintomas_normalizados, causas_probables[], nivel_riesgo, pruebas_taller_sugeridas}.

#### Scenario: JSON output validation
- **WHEN** AI analysis completes
- **THEN** system outputs valid JSON with all four top-level keys and correct type structure

### Requirement: Audio Transcription Accuracy
The system SHALL achieve minimum 90% transcription accuracy for Spanish language voice notes used as diagnostic input.

#### Scenario: Transcription quality check
- **WHEN** voice note is transcribed
- **THEN** system reports transcription confidence score above threshold for diagnostic use
