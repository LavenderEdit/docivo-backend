# Docivo Backend Roadmap — Self-Hosted Document Intelligence

This roadmap is dependency-ordered. Later phases must not bypass the foundations required for safe reproducibility and training governance.

## Phase 0 — Baseline hardening
**Goal:** make the current backend safe to extend.

Deliverables:
- environment-driven settings module
- stricter upload validation and size/page limits
- CORS configuration by environment
- task failures raised correctly instead of returning error payloads as successful Celery tasks
- basic tests for current public endpoints and tasks
- structured logging with `job_id`

Exit criteria:
- existing `/api/v1/tools/*` behavior remains compatible
- failed operations are visible as failed jobs
- tests establish a regression baseline

## Phase 1 — Modular document-processing architecture
**Goal:** remove OCR/provider coupling from `app/tasks.py`.

Deliverables:
- split routers/services/tasks by domain
- introduce `OCRProvider`
- implement `TesseractOCRProvider`
- add normalized `OCRRequest` / `OCRResult`
- explicit Celery queue routing
- `documents`, `ai`, and optional `office` queues

Exit criteria:
- Tesseract behavior works through provider abstraction
- no Unlimited-OCR dependencies are present in the CPU application image

## Phase 2 — Self-hosted Unlimited-OCR inference
**Goal:** enable private GPU intelligent OCR.

Deliverables:
- GPU Compose profile/service
- pinned `baidu/Unlimited-OCR` revision
- vLLM-based serving first; adapter should permit alternative runtime later
- `UnlimitedOCRProvider`
- internal health/readiness checks
- timeouts, retries, bounded concurrency, backpressure
- integration tests with mocked inference API

Exit criteria:
- a PDF/image can be processed through Unlimited-OCR end to end
- inference service is not publicly exposed
- GPU outage is reported/fallback-aware

## Phase 3 — Document Intelligence API
**Goal:** add a Docivo-owned intelligent parsing contract.

Deliverables:
- `POST /api/v1/intelligence/parse`
- optional `POST /api/v1/intelligence/extract`
- OCR mode: `fast | intelligent | auto`
- normalized text/Markdown/block output
- output artifacts
- initial deterministic document router

Exit criteria:
- clients do not depend on raw Baidu output
- routing reason and engine/model version are recorded

## Phase 4 — Durable jobs and object storage
**Goal:** remove Redis/local-disk as the only durable state.

Deliverables:
- PostgreSQL metadata store
- migration tooling
- durable `Job`, `OCRRun`, `Artifact` records
- MinIO/S3 abstraction
- job-oriented object key layout
- artifact retention/cleanup jobs

Exit criteria:
- job provenance survives Celery result expiry/restart
- API/worker can scale without requiring the same local filesystem

## Phase 5 — Feedback and correction capture
**Goal:** collect high-quality supervised OCR corrections.

Deliverables:
- feedback/correction entities
- API for correction submission
- prediction-vs-correction diff metadata
- verification/reviewer state
- training eligibility/consent field
- privacy/redaction pipeline hooks

Exit criteria:
- corrections can be captured without automatically entering training
- every correction has provenance and policy state

## Phase 6 — Dataset registry and governance
**Goal:** build reproducible training datasets.

Deliverables:
- immutable `TrainingSample`
- dataset manifests
- versioned train/validation/test splits
- deduplication/checksum checks
- leakage safeguards
- domain tags
- consent/privacy filters

Exit criteria:
- a dataset version can be reproduced from its manifest
- evaluation samples cannot silently leak into training

## Phase 7 — Training pipeline with ms-swift
**Goal:** produce Docivo-specific adapters safely.

Deliverables:
- isolated trainer image
- LoRA/QLoRA recipes for Unlimited-OCR
- training-run metadata
- checkpoint/artifact storage
- deterministic seed/config capture where feasible
- resource limits and failure recovery

Exit criteria:
- an approved dataset version can produce a versioned candidate adapter
- training never mutates the production model in place

## Phase 8 — Evaluation and model registry
**Goal:** prevent regressions from entering production.

Deliverables:
- frozen benchmark datasets
- CER/WER metrics
- structured-field/layout/table metrics where applicable
- latency/throughput/VRAM metrics
- candidate-vs-production comparison
- model/adaptor registry states
- explicit promote/reject/rollback workflow

Exit criteria:
- no model reaches production without evaluation evidence
- previous production version can be restored

## Phase 9 — Continuous learning loop
**Goal:** convert verified product usage into periodic model improvements.

Deliverables:
- scheduled/manual dataset build
- candidate training pipeline
- evaluation gate
- staging/canary mechanism
- explicit production promotion
- monitoring for quality drift

Exit criteria:
- new feedback can flow into a future model version without online per-request weight mutation

## Phase 10 — Domain specialization
**Goal:** create targeted advantages from Docivo data.

Potential adapters:
- `docivo-general`
- `docivo-invoices`
- `docivo-legal`
- `docivo-academic`
- `docivo-forms`

Potential Peru-specific evaluation domains:
- SUNAT-style invoices/receipts
- RUC/DNI field formats where lawful and appropriate
- local legal/administrative document layouts

Exit criteria:
- domain routing is evidence-driven and benchmarked against general model performance

## Phase 11 — Performance and production scaling
**Goal:** optimize cost and throughput after real measurements exist.

Candidate work:
- batching
- quantization if validated
- GPU-specific deployment profiles
- multi-GPU / replicas
- autoscaling strategy where infrastructure permits
- queue admission control
- benchmark-derived concurrency
- cache strategies where safe

Never optimize by guesswork; record baseline and post-change measurements.

## Phase 12 — Mature security/operations
**Goal:** production-grade operation.

Deliverables:
- authentication/authorization and tenant isolation as product requirements demand
- rate limits/quotas
- audit logs
- backup/restore for metadata and registries
- disaster-recovery runbook
- vulnerability/dependency scanning
- model supply-chain pinning/checksums
- secret management
- documented incident response
