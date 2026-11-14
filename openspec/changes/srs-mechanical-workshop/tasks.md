# Tasks

## Implementation Order

### 1. Database Models
- [ ] Create OrdenFalla model with fields: ticket, taller (FK), vehiculo (FK), mecanico_asignado (FK User), codigo_orden, kilometraje_ingreso, estado, etiquetas, token_publico, token_expira_en
- [ ] Create EvidenciaSintoma model with fields: orden (FK), archivo_audio, imagen, narrativa_cliente, diagnostico_ia_json, nivel_riesgo
- [ ] Create ItemPresupuestoRepuestos model with fields: orden (FK), tipo (REPUESTO / MANO_OBRA), descripcion, cantidad, precio_unitario, aprobado_cliente
- [ ] Create migracions for all new models

### 2. AI Processing Service
- [ ] Implement multimodal AI pipeline: audio transcription + image analysis + vehicle data cross-reference
- [ ] Develop symptom normalization taxonomy for mechanical components
- [ ] Build probable cause ranking algorithm with probability percentages
- [ ] Implement risk level classification (PUEDE_RODAR, PRECAUCION, NO_MOVER_GRUA)
- [ ] Create suggested technical tests with procedures and expected values

### 3. Workshop Management CRUD
- [ ] Implement order creation form with vehicle data capture
- [ ] Develop status workflow engine: PRE_DIAGNOSTICO -> EN_TALLER -> ESPERA_REPUESTO -> LISTO -> ENTREGADO
- [ ] Create mechanic assignment interface
- [ ] Build budget management: add/remove parts and labor items with approval
- [ ] Implement order search and filtering by status, vehicle, mechanic

### 4. PDF Report Generation
- [ ] Design HTML templates for workshop reports using xhtml2pdf
- [ ] Implement PDF generation endpoint rendering templates with order data
- [ ] Ensure PDF generation completes within 30 seconds
- [ ] Test PDF output with complete order data and evidence

### 5. Report Distribution
- [ ] Implement Telegram Bot API integration for PDF delivery
- [ ] Configure SMTP email server connection for report distribution
- [ ] Develop distribution method per-order selection: Telegram, Email, both, neither
- [ ] Implement retry logic for delivery failures
- [ ] Add local PDF download as fallback option

### 6. UI / Front-end
- [ ] Create vehicle registration form with all data fields
- [ ] Develop symptom submission interface: voice recording, photo upload, text narrative
- [ ] Design order status dashboard with workflow visualization
- [ ] Build PDF report preview and download interface
- [ ] Configure distribution method selection per order

### 7. Testing and Validation
- [ ] Write unit tests for model validation
- [ ] Develop integration tests for AI processing pipeline
- [ ] Create end-to-end tests for order lifecycle
- [ ] Test PDF generation under various data conditions
- [ ] Validate Telegram/Email delivery in test environment

### 8. Deployment and Documentation
- [ ] Configure environment variables for Telegram bot token
- [ ] Set up SMTP email credentials and test connection
- [ ] Deploy database migrations to production
- [ ] Write user manual for workshop staff
- [ ] Document AI model limitations and risk classification criteria
