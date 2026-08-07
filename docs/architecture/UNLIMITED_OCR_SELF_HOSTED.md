# Unlimited-OCR Self-Hosted Architecture

## Decision
Docivo will self-host `baidu/Unlimited-OCR` as an internal GPU inference service. It will not depend on Baidu Cloud or another paid OCR API for the core intelligent OCR path.

Tesseract remains available as a CPU engine and fallback. Unlimited-OCR is added as a second provider behind a Docivo-owned abstraction.

## Upstream facts used by this design
- Upstream repository/model: `baidu/Unlimited-OCR`.
- License: MIT.
- Public model artifacts are available from Hugging Face/ModelScope.
- Upstream supports vLLM inference.
- Upstream also documents SGLang and Transformers workflows.
- Upstream announced `ms-swift` training support.

Always pin a known-compatible upstream revision in deployment configuration rather than relying on `latest`/`main` behavior.

## Runtime separation

### Existing CPU application image
Keep Python 3.11 initially for:
- FastAPI
- Celery
- Redis client
- PyMuPDF
- Tesseract/pytesseract
- pdf2docx
- LibreOffice

### GPU inference image
Dedicated service containing:
- Unlimited-OCR model runtime
- vLLM preferred for initial serving
- CUDA/runtime required by the chosen image
- model cache volume
- health/readiness endpoint or compatible readiness probe

The API and CPU workers communicate with inference over the private Docker/network boundary.

### GPU training image
Separate from inference and invoked only for training workflows. Contains:
- `ms-swift`
- training dependencies
- access to approved dataset/object storage
- access to model registry/object storage

Inference must remain available while training is running; ideally training uses separate GPU capacity or runs during explicitly scheduled maintenance/capacity windows.

## Suggested Compose profile structure

Development target:

```text
redis
postgres
minio
api
worker-document
worker-ai
ocr-inference  [profile: gpu]
trainer        [profile: training, on demand]
```

`worker-office` can be split when Office jobs materially compete with document processing.

## Network policy
Public:
- FastAPI only.

Private only:
- Redis
- PostgreSQL
- MinIO management/data endpoints unless explicitly proxied
- vLLM/SGLang inference endpoint
- trainer control plane

Never publish the raw inference server to the internet.

## Configuration contract
Recommended environment variables:

```text
DOCIVO_OCR_DEFAULT_MODE=auto
DOCIVO_OCR_FAST_PROVIDER=tesseract
DOCIVO_OCR_INTELLIGENT_PROVIDER=unlimited-ocr
UNLIMITED_OCR_BASE_URL=http://ocr-inference:8000
UNLIMITED_OCR_MODEL=baidu/Unlimited-OCR
UNLIMITED_OCR_REVISION=<pinned revision>
UNLIMITED_OCR_TIMEOUT_SECONDS=<bounded value>
UNLIMITED_OCR_MAX_RETRIES=<small bounded value>
UNLIMITED_OCR_MAX_CONCURRENCY=<benchmark-derived>
POSTGRES_DSN=...
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET_DOCS=docivo-documents
S3_BUCKET_MODELS=docivo-models
S3_BUCKET_DATASETS=docivo-datasets
```

Secrets must not be committed.

## Request path

```text
POST /api/v1/intelligence/parse
  -> validate upload
  -> persist source artifact
  -> create durable Job record
  -> enqueue queue=ai or queue=documents
  -> worker analyzes/renders document
  -> UnlimitedOCRProvider calls private inference service when selected
  -> normalize output
  -> persist result artifacts + metadata
  -> mark Job success/failure
```

## Queue model
Use explicit Celery routing.

Recommended queues:
- `documents`: PyMuPDF, Tesseract, PDF/DOCX transforms.
- `office`: LibreOffice-heavy jobs when separated.
- `ai`: Unlimited-OCR orchestration and normalization.
- `maintenance`: cleanup, dataset preparation, non-request-path background work.

Do not execute CUDA inference in a generic Celery process.

## Artifact layout
Logical object-storage layout:

```text
jobs/{job_id}/source/{filename}
jobs/{job_id}/pages/{page}.png
jobs/{job_id}/raw/{provider}.json
jobs/{job_id}/outputs/result.json
jobs/{job_id}/outputs/result.md
jobs/{job_id}/outputs/result.docx
feedback/{job_id}/{feedback_id}.json
datasets/{dataset_name}/{version}/manifest.json
models/{model_name}/{version}/...
```

Raw provider outputs should follow retention/privacy policy.

## Persistent metadata
Add PostgreSQL before the learning loop. Suggested entities:
- `jobs`
- `job_artifacts`
- `ocr_runs`
- `feedback`
- `training_samples`
- `datasets`
- `dataset_samples`
- `training_runs`
- `model_versions`
- `evaluations`
- `model_promotions`

Celery result backend is not sufficient as the canonical long-term audit store.

## Failure/fallback semantics
`fast`:
- Tesseract failure -> job failure.

`intelligent`:
- Unlimited-OCR failure -> job failure unless `allow_fallback=true`.

`auto`:
- router may use native extraction, Tesseract, or Unlimited-OCR.
- if Unlimited-OCR is unavailable and policy permits, fall back to Tesseract and record a warning and routing reason.

Never silently claim intelligent OCR succeeded when a fallback engine actually produced the output.

## Health model
Expose aggregated Docivo health separately from raw dependencies.

Suggested endpoints:
- `GET /health/live`
- `GET /health/ready`

Readiness may report:
- Redis connectivity
- metadata DB connectivity
- object storage connectivity
- inference availability

Inference unavailability should not necessarily make all of Docivo unready if CPU tools remain usable; readiness should expose degraded capability explicitly.

## Observability
Track at minimum:
- jobs by type/status
- queue depth
- task duration
- OCR engine selection counts
- inference latency p50/p95
- pages/minute
- GPU utilization/VRAM
- retry/failure/fallback rates
- model/adaptor version usage
- feedback/correction rate
- dataset/training/evaluation audit events

## Deployment phases

### Phase A — CPU compatibility
Refactor providers/queues with no behavior regression.

### Phase B — GPU intelligent OCR
Add inference service and intelligent endpoints.

### Phase C — durable platform
PostgreSQL, MinIO/S3, job metadata, retention/cleanup.

### Phase D — feedback and learning
Corrections, consent/eligibility, datasets, training, evaluation, registry, promotion.

### Phase E — optimization
Auto-router improvements, domain adapters, batching, quantization/capacity tuning, multi-GPU if justified by benchmarks.

## Capacity notes
Do not hard-code a claimed minimum GPU until benchmarking the exact upstream revision/runtime. Establish a supported-hardware matrix from measured tests. The model artifacts themselves are several GB; operational VRAM requirements can exceed raw weight size because of runtime, KV cache, image processing, batching, and context.

## Upgrade policy
Before changing any of these:
- Unlimited-OCR revision
- vLLM image/runtime
- CUDA base
- ms-swift version
- LoRA adapter

run the evaluation suite and document compatibility. Production upgrades must be versioned and reversible.
