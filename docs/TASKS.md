# Docivo Implementation Tasks

This file is the working checklist behind the GitHub issues. Issues are the execution units; this document preserves the full dependency map for humans and AI agents.

## T0 — Repository baseline and safety
- [ ] Add centralized settings/configuration.
- [ ] Move CORS origins to configuration.
- [ ] Add upload extension/MIME validation.
- [ ] Add configurable maximum file size and maximum PDF page count.
- [ ] Ensure Celery task exceptions produce task `FAILURE` instead of business-error payloads returned as `SUCCESS`.
- [ ] Add structured logging with `job_id`, task name, engine and duration.
- [ ] Add baseline tests for existing endpoints.

## T1 — Refactor application boundaries
- [ ] Create router modules instead of concentrating HTTP routes in `app/main.py`.
- [ ] Create service modules for PDF, Office and OCR logic.
- [ ] Split Celery tasks by workload domain.
- [ ] Keep endpoint compatibility.
- [ ] Document import/dependency direction.

## T2 — OCR provider abstraction
- [ ] Define `OCRProvider` interface/protocol.
- [ ] Define normalized `OCRRequest`.
- [ ] Define normalized `OCRResult` / page/block models.
- [ ] Implement Tesseract provider.
- [ ] Refactor current OCR tasks to use provider.
- [ ] Unit-test provider behavior.

## T3 — Celery routing
- [ ] Declare `documents` queue.
- [ ] Declare `ai` queue.
- [ ] Declare `office` queue if LibreOffice is split immediately.
- [ ] Route task modules to queues.
- [ ] Add queue-specific worker commands in Compose.
- [ ] Set task time limits and retry policy intentionally.

## T4 — Unlimited-OCR inference service
- [ ] Choose/pin upstream Unlimited-OCR revision.
- [ ] Pin vLLM image/runtime known to support selected revision.
- [ ] Add GPU Compose profile.
- [ ] Configure NVIDIA Container Toolkit usage.
- [ ] Mount persistent model cache.
- [ ] Keep inference port on private network only.
- [ ] Add health/readiness probe.
- [ ] Add model warmup strategy.
- [ ] Document GPU compatibility matrix after benchmarking.

## T5 — Unlimited-OCR provider client
- [ ] Implement internal HTTP client.
- [ ] Configure base URL, model revision, timeout, retry and concurrency.
- [ ] Map images/PDF-rendered pages to upstream request format.
- [ ] Normalize response to Docivo schema.
- [ ] Strip/translate provider-specific markers.
- [ ] Capture inference metadata and warnings.
- [ ] Mock inference in tests.
- [ ] Add integration test against GPU profile when available.

## T6 — Document Intelligence API
- [ ] Add `/api/v1/intelligence/parse`.
- [ ] Support `mode=fast|intelligent|auto`.
- [ ] Support `allow_fallback`.
- [ ] Return asynchronous `job_id`.
- [ ] Produce normalized JSON artifact.
- [ ] Produce Markdown artifact where meaningful.
- [ ] Preserve existing `/tools/ocr` and `/tools/ocr-to-word` behavior.

## T7 — Auto router v1
- [ ] Inspect native PDF text coverage.
- [ ] Detect scan/image-only PDFs.
- [ ] Calculate simple layout/complexity heuristics.
- [ ] Define deterministic routing thresholds.
- [ ] Record route decision and reason.
- [ ] Benchmark router decisions against a labeled sample set.

## T8 — PostgreSQL metadata
- [ ] Add DB layer and migration tooling.
- [ ] Create `jobs` table/entity.
- [ ] Create `job_artifacts`.
- [ ] Create `ocr_runs`.
- [ ] Persist task lifecycle events.
- [ ] Keep Celery backend as execution-state mechanism, not canonical audit store.

## T9 — Object storage
- [ ] Add S3-compatible storage interface.
- [ ] Add MinIO to development Compose.
- [ ] Create document/model/dataset buckets.
- [ ] Move source/output persistence behind storage abstraction.
- [ ] Add signed/internal artifact retrieval strategy.
- [ ] Add retention and cleanup tasks.

## T10 — Feedback/correction system
- [ ] Add feedback/correction persistence.
- [ ] Add correction submission endpoint.
- [ ] Store original prediction and corrected target references.
- [ ] Store reviewer/verification state.
- [ ] Add `training_eligible` policy state.
- [ ] Add explicit consent/terms metadata where product flow requires it.
- [ ] Add audit history.

## T11 — Privacy and training eligibility
- [ ] Implement policy engine/checks for dataset inclusion.
- [ ] Define PII redaction/anonymization hooks.
- [ ] Prevent unconsented samples entering training datasets.
- [ ] Add deletion/retention propagation rules.
- [ ] Add provenance and checksum fields.

## T12 — Dataset registry
- [ ] Create `training_samples`.
- [ ] Create `datasets` and membership records.
- [ ] Create immutable manifests.
- [ ] Add dataset versioning.
- [ ] Add train/validation/test split generation.
- [ ] Add duplicate/near-duplicate controls.
- [ ] Add leakage checks.
- [ ] Add domain/language/document-type tags.

## T13 — Trainer service
- [ ] Add isolated `trainer` image/profile.
- [ ] Pin `ms-swift` version.
- [ ] Implement LoRA/QLoRA training recipe for pinned Unlimited-OCR revision.
- [ ] Read only approved dataset versions.
- [ ] Write candidate adapter/checkpoint artifacts.
- [ ] Persist training configuration, metrics and logs.
- [ ] Support failed-run cleanup/retry.

## T14 — Evaluation framework
- [ ] Create frozen benchmark datasets.
- [ ] Implement CER.
- [ ] Implement WER.
- [ ] Implement structured-field exact/fuzzy metrics where applicable.
- [ ] Add layout/table evaluation for selected benchmark sets.
- [ ] Capture latency, throughput and GPU memory metrics.
- [ ] Compare candidate with current production version.
- [ ] Produce machine-readable evaluation report.

## T15 — Model registry and promotion
- [ ] Create model/version metadata.
- [ ] Track base revision + adapter version.
- [ ] Define states: candidate/staging/production/retired/rejected.
- [ ] Add promotion rules.
- [ ] Add rollback.
- [ ] Prevent mutable overwrite of released versions.
- [ ] Record who/what promoted a model and evaluation evidence.

## T16 — Continuous-learning workflow
- [ ] Build eligible-sample selection job.
- [ ] Build dataset-version creation workflow.
- [ ] Trigger/manual training workflow.
- [ ] Evaluate candidate automatically after training.
- [ ] Require explicit promotion unless a later policy defines safe automated gates.
- [ ] Add staging/canary support.
- [ ] Monitor post-promotion drift/error signals.

## T17 — Domain adapters
- [ ] General adapter benchmark.
- [ ] Invoice adapter dataset/benchmark.
- [ ] Legal adapter dataset/benchmark.
- [ ] Academic adapter dataset/benchmark.
- [ ] Forms adapter dataset/benchmark.
- [ ] Optional Peru-specific benchmark categories with privacy/legal review.
- [ ] Add domain-router logic only after adapters prove useful.

## T18 — Observability
- [ ] Metrics endpoint/exporter.
- [ ] Queue depth metrics.
- [ ] Engine/routing metrics.
- [ ] Inference p50/p95.
- [ ] Pages/minute.
- [ ] GPU utilization/VRAM monitoring integration.
- [ ] Failure/retry/fallback rates.
- [ ] Dataset/training/model promotion audit metrics.

## T19 — Production security and operations
- [ ] Authentication/authorization appropriate to product scope.
- [ ] Tenant-aware artifact access if multi-tenant.
- [ ] Rate limits/quotas.
- [ ] Private service networking.
- [ ] Secret management.
- [ ] Dependency/model supply-chain pinning and checksum verification.
- [ ] Backup/restore.
- [ ] Disaster recovery runbook.
- [ ] Security scanning.

## Recommended task dependency chain

```text
T0 -> T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7
                    |                 |
                    +------> T8 -> T9 +-> T10 -> T11 -> T12 -> T13 -> T14 -> T15 -> T16
                                                                                   |
                                                                                   -> T17
T18 begins during T0 and expands throughout.
T19 begins during T0 and matures before production exposure.
```
