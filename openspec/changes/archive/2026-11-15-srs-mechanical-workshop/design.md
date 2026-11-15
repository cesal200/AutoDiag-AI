# Design

## Context

AutoDiag AI is a web application for mechanical workshop management with AI pre-diagnosis, following Django MVT architecture.## Goals / Non-Goals

**Goals:**
- Implement complete repair order lifecycle (PRE_DIAGNOSTICO -> EN_TALLER -> ESPERA_REPUESTO -> LISTO -> ENTREGADO)
- Provide multimodal AI analysis within 5 minutes
- Generate PDF reports in under 30 seconds
- Support distribution via Telegram and/or Email per order
- Maintain risk level classification (PUEDE_RODAR, PRECAUCION, NO_MOVER_GRUA)

**Non-Goals:**
- Real-time vehicle monitoring or GPS tracking
- Integration with external repair databases beyond Make/Model/Year
- Mobile native application (web-only)
- Advanced CRDT conflict resolution for offline sync
- AI model training or retraining infrastructure

## Decisions

### Django MVT Architecture
- **Choice**: Django framework with Model-View-Template pattern
- **Rationale**: Rapid development, built-in admin, ORM compatibility, Python ecosystem for AI integration
- **Alternatives**: Flask/FastAPI (less admin), Node.js (different language ecosystem)

### Multimodal AI Processing Pipeline
- **Choice**: Process voice + images + structured data together
- **Rationale**: Client narrative + vehicle specs + visual evidence provides comprehensive diagnosis
- **Alternatives**: Text-only analysis (less accurate), single-modality (insufficient)

### Risk Level Classification
- **Choice**: Three-tier classification (PUEDE_RODAR, PRECAUCION, NO_MOVER_GRUA)
- **Rationale**: Clear risk communication for drivers, prevents dangerous operation
- **Alternatives**: Continuous scale (overly complex), binary (too simplistic)

### PDF Report Generation
- **Choice**: xhtml2pdf with HTML templates
- **Rationale**: Existing library, familiar HTML/CSS, generates print-ready documents
- **Alternatives**: ReportLab (lower-level), WeasyPrint (similar, different API)

### Distribution Methods
- **Choice**: Per-order selection of Telegram, Email, both, or neither
- **Rationale**: Workshop preferences vary; some prefer digital, some paper
- **Alternatives**: Mandatory single method (reduces flexibility)

## Risks / Trade-offs

[Risk] AI transcription errors in Spanish technical terminology
- **Mitigation**: Implement validation step, allow manual correction before AI processing

[Risk] PDF template inconsistencies across browsers
- **Mitigation**: Test templates in Chrome, Firefox, Safari; use standardized CSS

[Risk] AI probability inaccuracies leading to misdiagnosis
- **Mitigation**: Display probability as guidance only, not definitive diagnosis

[Risk] Telegram/Email delivery failures
- **Mitigation**: Implement retry logic, notify user on delivery failure, provide local PDF download

## Open Questions

- What is the fallback when AI service is unavailable? (Documented as non-goal for MVP)
- Should client narrative be required or optional? (Design decision pending user feedback)
- What is the maximum file size for photo/audio uploads? (Can be addressed in implementation)
