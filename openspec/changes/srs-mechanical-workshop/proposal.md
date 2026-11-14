# Proposal

## Why

The operational daily routine of mechanical, electromechanical, and automotive diagnostic centers faces a critical bottleneck: the time required for technical triage and symptom reception. Customers often imprecisely report symptoms (noises, vibrations, warning lights), causing workshops to lose hours identifying the probable cause and estimating spare parts. This proposal addresses the need for AutoDiag AI, a web application that integrates multimodal artificial intelligence to automate pre-diagnosis, reduce reception time, and optimize workshop resource allocation.

## What Changes

- Creation of a comprehensive Software Requirements Specification (SRS) following IEEE 830-1998 standard for the AutoDiag AI system
- Definition of multimodal AI processing pipeline (voice transcription + image analysis + vehicle specifications)
- Establishment of repair order lifecycle management with AI-assisted pre-diagnosis
- Implementation of PDF report generation and distribution via Telegram and Email
- Definition of database schema for orders, symptoms, evidence, and budget items

## Capabilities

### New Capabilities

- \workshop-management\: Covers the complete repair order lifecycle (creation, status tracking, mechanic assignment, budget management) with AI pre-diagnosis integration
- \i-pre-diagnosis\: Covers the multimodal AI processing pipeline that transforms raw client inputs (voice, images, vehicle data) into normalized symptoms, probable causes with probabilities, risk levels, and suggested technical tests
- eport-distribution\: Covers PDF report generation using xhtml2pdf + HTML templates, and distribution via Telegram Bot API and SMTP email

### Modified Capabilities

- None (this is a new system implementation)

## Impact

- **Code**: Django MVT architecture implementation with new models (OrdenFalla, EvidenciaSintoma, ItemPresupuesto, etc.)
- **APIs**: JSON output format for AI diagnostic results, HTML template rendering for PDF generation
- **Dependencies**: xhtml2pdf library, Telegram Bot API, email SMTP service
- **Systems**: Web forms for vehicle data capture, multimedia upload (photos, audio), status workflow engine (PRE_DIAGNOSTICO  EN_TALLER  ESPERA_REPUESTO  LISTO  ENTREGADO)
