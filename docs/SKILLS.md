# Skills Required for the Docivo OCR Roadmap

This document defines the technical competencies an engineer or AI coding agent should possess before taking ownership of each workstream.

## Core backend skills
- Python 3.11+
- FastAPI routing, dependency injection, validation, exception handling
- Pydantic schemas/settings
- async HTTP clients and timeout/retry semantics
- clean architecture / ports-and-adapters style boundaries
- testing with pytest and API test clients
- structured logging and observability

## Asynchronous processing
- Celery task lifecycle
- queue routing and worker specialization
- Redis broker/result-backend behavior
- retries, idempotency, task time limits and failure semantics
- backpressure and bounded concurrency
- distributed-job observability

## PDF/document processing
- PyMuPDF/fitz
- rasterization and DPI tradeoffs
- PDF native text inspection
- Tesseract/pytesseract
- DOCX/PDF conversion constraints
- LibreOffice headless execution
- preservation of layout and document metadata

## GPU inference and serving
Required for Unlimited-OCR integration:
- NVIDIA drivers and NVIDIA Container Toolkit
- CUDA/runtime compatibility concepts
- vLLM serving and OpenAI-compatible APIs
- GPU memory constraints, batching and concurrency
- model caching and warmup
- private-network inference services
- health/readiness design
- basic SGLang familiarity is useful as a future alternative

## Vision-language OCR / document intelligence
- multimodal model inference
- page/image preprocessing
- multi-page parsing concepts
- normalization of model-specific output into stable schemas
- document-layout representation
- evaluation of OCR vs document parsing
- hallucination/error handling for generative OCR systems

## Data engineering for learning
- immutable dataset manifests
- train/validation/test splitting
- checksums and provenance
- duplicate and leakage detection
- object storage (S3/MinIO)
- PostgreSQL schema design and migrations
- dataset versioning

## Fine-tuning skills
Required from the training phase onward:
- supervised fine-tuning concepts
- LoRA and QLoRA
- `ms-swift`
- training configuration/version pinning
- checkpoint/adaptor management
- reproducibility and deterministic configuration where practical
- GPU training resource management
- avoiding catastrophic forgetting and feedback-loop contamination

## ML evaluation
- CER and WER
- exact/fuzzy structured-field metrics
- benchmark design
- frozen holdout datasets
- regression gates
- latency/throughput benchmarking
- VRAM monitoring
- model comparison and promotion decisions

## MLOps/model lifecycle
- model registry concepts
- versioned adapters/checkpoints
- candidate/staging/production states
- promotion and rollback
- canary/staging deployments
- drift monitoring
- auditability of training and promotion events

## Security/privacy
- handling untrusted document uploads
- MIME/file validation and size limits
- path traversal prevention
- service-network isolation
- secret management
- PII minimization/redaction/anonymization
- retention/deletion workflows
- consent and training-eligibility enforcement
- tenant isolation if/when Docivo becomes multi-tenant

## DevOps/self-hosting
- Docker and Docker Compose
- multi-service networking
- persistent volumes
- PostgreSQL operations
- MinIO/S3-compatible storage
- healthchecks and restart policies
- backups and restore procedures
- metrics/log collection
- CI for CPU tests and optional GPU integration tests

## Skills by roadmap phase

| Phase | Minimum skills |
|---|---|
| 0 Baseline | Python, FastAPI, Celery, pytest, security basics |
| 1 Modularization | architecture, provider pattern, Celery routing |
| 2 Unlimited-OCR | Docker GPU, NVIDIA, vLLM, multimodal inference |
| 3 Intelligence API | FastAPI contracts, OCR normalization, document parsing |
| 4 Durable platform | PostgreSQL, migrations, S3/MinIO |
| 5 Feedback | API design, data provenance, privacy |
| 6 Datasets | data engineering, versioning, leakage prevention |
| 7 Training | ms-swift, LoRA/QLoRA, GPU training |
| 8 Evaluation | OCR metrics, benchmarking, MLOps |
| 9 Continuous learning | orchestration, model registry, rollback/canary |
| 10+ | domain ML, production scaling, security operations |

## Guidance for AI agents
An AI agent must not claim a phase is complete if it cannot validate the critical technology boundary involved. Examples:
- Do not implement a fake GPU healthcheck without understanding the actual inference server endpoint.
- Do not invent ms-swift CLI flags; verify them against the pinned version/upstream documentation during implementation.
- Do not guess vLLM compatibility tags; pin and test a concrete image/version.
- Do not fabricate OCR quality numbers; benchmark them.
- Do not create training samples from production documents without passing the documented eligibility policy.
