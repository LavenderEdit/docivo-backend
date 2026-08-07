# AGENTS.md — Docivo Backend

## Purpose
This file is the primary context contract for any AI coding agent working on `docivo-backend`.

Docivo is evolving from a document-conversion API into a self-hosted document-intelligence platform. The strategic OCR direction is to retain Tesseract for fast/CPU fallback workloads and add `baidu/Unlimited-OCR` as the primary intelligent OCR/document-parsing engine through an isolated GPU inference service.

## Current repository baseline
- FastAPI API in `app/main.py`.
- Celery task definitions currently concentrated in `app/tasks.py`.
- Redis is both broker and result backend.
- One generic Celery worker currently handles all task types.
- PyMuPDF is used for PDF rendering/manipulation.
- Tesseract/pytesseract is the current OCR engine.
- pdf2docx handles PDF -> DOCX.
- LibreOffice headless handles Word -> PDF.
- Local disk storage currently uses `storage/uploads` and `storage/processed`.
- Docker Compose currently starts `redis`, `api`, and `worker`.

## Target architecture
Do NOT embed Unlimited-OCR, CUDA, Torch, vLLM, or training dependencies into the existing generic API/worker image.

Target services:
1. `api`: FastAPI orchestration and HTTP contract.
2. `redis`: broker/result backend initially.
3. `worker-document`: CPU document-processing queue.
4. `worker-office`: optional CPU office-conversion queue.
5. `worker-ai`: orchestration for AI jobs; does not own model weights.
6. `ocr-inference`: isolated NVIDIA GPU service hosting `baidu/Unlimited-OCR`, preferably behind vLLM/OpenAI-compatible HTTP.
7. `object-storage`: MinIO/S3-compatible storage in the production architecture; local disk may remain for development.
8. `metadata-db`: PostgreSQL for persistent job/model/dataset metadata when the learning pipeline is introduced.
9. `trainer`: isolated, on-demand GPU training runtime using `ms-swift`; never part of request-path inference.
10. `model-registry`: logical registry backed by object storage + PostgreSQL metadata.

## Non-negotiable design rules
- Preserve existing public endpoints unless a migration issue explicitly changes them.
- Introduce provider abstractions before adding Unlimited-OCR integration.
- Never update model weights after every user request.
- Learning is batch-based, versioned, evaluated, and explicitly promoted.
- Do not train on user documents by default.
- Training samples require explicit policy eligibility/consent and provenance.
- Keep the Baidu base model immutable and version-pinned.
- Prefer LoRA/QLoRA adapters before considering full fine-tuning.
- Every model/adaptor deployment must be reproducible by version.
- A candidate model must beat or meet the production baseline on approved evaluation gates before promotion.
- Tesseract remains available as a CPU fallback/fast engine.
- Do not return raw provider-specific output as the public Docivo API contract; normalize it into Docivo-owned schemas.
- GPU failures must degrade gracefully when the request mode permits fallback.
- All long-running work remains asynchronous.

## Intended OCR modes
- `fast`: Tesseract/CPU.
- `intelligent`: Unlimited-OCR/GPU.
- `auto`: document router chooses native extraction, Tesseract, or Unlimited-OCR based on document characteristics and configured policy.

## Intended API direction
Keep `/api/v1/tools/*` compatibility and add document-intelligence endpoints under `/api/v1/intelligence/*`.

Initial intended endpoints:
- `POST /api/v1/intelligence/parse`
- `POST /api/v1/intelligence/extract`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/downloads/{job_id}`

Future feedback endpoints:
- `POST /api/v1/intelligence/jobs/{job_id}/feedback`
- `POST /api/v1/intelligence/jobs/{job_id}/corrections`

## Canonical internal interfaces
Create interfaces approximately equivalent to:
- `OCRProvider`
- `TesseractOCRProvider`
- `UnlimitedOCRProvider`
- `DocumentRouter`
- `DocumentParser`
- `LearningSampleService`
- `DatasetRegistry`
- `ModelRegistry`
- `EvaluationService`

Names may change if the codebase develops a clearer convention, but responsibilities must remain separated.

## Normalized result contract
Internal/public DTOs should be Docivo-owned and include, where applicable:
- job/document identifiers
- engine/provider
- base-model version
- adapter/version
- page count
- normalized text
- markdown
- structural blocks/layout information
- warnings
- timing metrics
- provenance
- output artifact references

Do not couple clients to Baidu-specific tokens or detection markers.

## Continuous-learning policy
The learning loop is:
1. Inference.
2. Optional human correction/verification.
3. Eligibility and privacy filtering.
4. Immutable training-sample creation with provenance.
5. Dataset version creation.
6. LoRA/QLoRA training with `ms-swift`.
7. Evaluation against frozen benchmark sets.
8. Candidate registration.
9. Explicit promotion to production.
10. Rollback support.

Never perform automatic per-request online weight updates.

## Data governance
At minimum track:
- data origin
- user/account or tenant scope where applicable
- consent/eligibility state
- retention policy
- PII redaction/anonymization state
- checksum of source and corrected targets
- annotator/reviewer provenance
- dataset version membership

No private document may enter a training dataset merely because it was processed by OCR.

## Deployment constraints
- Self-hosted is the default design target.
- Unlimited-OCR code/model are MIT-licensed upstream, but retain required notices and pin upstream versions.
- Production GPU inference should be isolated from CPU workers.
- Use NVIDIA Container Toolkit for GPU containers.
- Prefer health/readiness checks and explicit model warmup.
- Configure bounded concurrency and queue backpressure around GPU inference.
- Never expose the internal vLLM/SGLang inference port directly to the public internet.

## Repository migration principle
Refactor incrementally. Do not rewrite the whole backend in one issue. Each issue should leave the repository runnable and should include tests where practical.

## Source documents
Read these before implementing OCR/AI work:
- `docs/AI_CONTEXT.md`
- `docs/architecture/UNLIMITED_OCR_SELF_HOSTED.md`
- `docs/ROADMAP.md`
- `docs/TASKS.md`
- `docs/SKILLS.md`
- `docs/DATA_LEARNING_POLICY.md`

## Definition of done for AI-generated changes
A change is not done unless:
- architecture boundaries above remain intact;
- public compatibility impact is documented;
- configuration is environment-driven;
- errors are observable and actionable;
- new integration logic has tests/mocks where feasible;
- docs are updated if contracts or deployment assumptions changed;
- no training-data ingestion bypasses eligibility/privacy policy.
