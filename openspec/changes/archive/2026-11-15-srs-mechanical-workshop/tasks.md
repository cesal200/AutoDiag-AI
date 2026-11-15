# Tasks

## Implementation Order

### 1. Database Models
- [x] Create OrdenFalla model with fields: ticket, taller (FK), vehiculo (FK), mecanico_asignado (FK User), codigo_orden, kilometraje_ingreso, estado, etiquetas, token_publico, token_expira_en
- [x] Create EvidenciaSintoma model with fields: orden (FK), archivo_audio, imagen, narrativa_cliente, diagnostico_ia_json, nivel_riesgo
- [x] Create ItemPresupuestoRepuestos model with fields: orden (FK), tipo (REPUESTO / MANO_OBRA), descripcion, cantidad, precio_unitario, aprobado_cliente
- [x] Create migracions for all new models

### 2. AI Processing Service
- [x] Implement multimodal AI pipeline: audio transcription + image analysis + vehicle data cross-reference
- [x] Develop symptom normalization taxonomy for mechanical components
- [x] Build probable cause ranking algorithm with probability percentages
- [x] Implement risk level classification (PUEDE_RODAR, PRECAUCION, NO_MOVER_GRUA)
- [x] Create suggested technical tests with procedures and expected values

### 3. Workshop Management CRUD
- [x] Implement order creation form with vehicle data capture
- [x] Develop status workflow engine: PRE_DIAGNOSTICO -> EN_TALLER -> ESPERA_REPUESTO -> LISTO -> ENTREGADO
- [x] Create mechanic assignment interface
- [x] Build budget management: add/remove parts and labor items with approval
- [x] Implement order search and filtering by status, vehicle, mechanic

### 4. PDF Report Generation
- [x] Design HTML templates for workshop reports using xhtml2pdf
- [x] Implement PDF generation endpoint rendering templates with order data
- [x] Ensure PDF generation completes within 30 seconds
- [x] Test PDF output with complete order data and evidence

### 5. Report Distribution
- [x] Implement Telegram Bot API integration for PDF delivery
- [x] Configure SMTP email server connection for report distribution
- [x] Develop distribution method per-order selection: Telegram, Email, both, neither
- [x] Implement retry logic for delivery failures
- [x] Add local PDF download as fallback option

### 6. UI / Front-end
- [x] Create vehicle registration form with all data fields
- [x] Develop symptom submission interface: voice recording, photo upload, text narrative
- [x] Design order status dashboard with workflow visualization
- [x] Build PDF report preview and download interface
- [x] Configure distribution method selection per order

### 7. Testing and Validation
- [x] Write unit tests for model validation
- [x] Develop integration tests for AI processing pipeline
- [x] Create end-to-end tests for order lifecycle
- [x] Test PDF generation under various data conditions
- [x] Validate Telegram/Email delivery in test environment

### 8. Deployment and Documentation
- [x] Configure environment variables for Telegram bot token
- [ ] Set up SMTP email credentials and test connection
- [ ] Deploy database migrations to production
- [x] Write user manual for workshop staff
- [x] Document AI model limitations and risk classification criteria
