# Docivo AI Context

## Strategic objective
Evolve Docivo from a general document-processing backend into a self-hosted document-intelligence platform with two OCR tiers:

- **Fast OCR:** Tesseract on CPU for low-cost/simple OCR and fallback.
- **Intelligent OCR:** Baidu Unlimited-OCR on a dedicated GPU inference service for complex layouts, long/multi-page documents, structured extraction, and future domain specialization.

The system must remain deployable without paid OCR APIs. External cloud OCR services are not required by the target architecture.

## Why Unlimited-OCR
The upstream `baidu/Unlimited-OCR` project is MIT licensed and supports local inference. The upstream project currently supports Transformers, vLLM, SGLang, PDF/image processing workflows, and training through `ms-swift`.

Docivo must consume the model through an internal provider boundary instead of coupling API/business code directly to the upstream runtime.

## Current technical debt to address first
The current backend has the following scaling constraints:

1. `app/main.py` owns routing and upload orchestration directly.
2. `app/tasks.py` contains unrelated OCR, preview, conversion, text extraction, and Office operations.
3. One Celery application/worker processes all workloads.
4. OCR is directly implemented with `pytesseract` inside task functions.
5. There is no persistent job metadata store beyond Celery result state.
6. Local disk paths are the only artifact persistence model.
7. There are no provider interfaces, model registry, dataset registry, evaluation pipeline, or training governance mechanisms.
8. Errors inside many tasks are returned as `{status: error}` instead of raising task failures, which can make Celery report `SUCCESS` for failed business operations.
9. CORS is currently permissive (`*`) and should be environment-configured before production exposure.

## Target bounded contexts

### API/Orchestration
Responsibilities:
- authentication/authorization when added
- request validation
- upload registration
- job creation
- job status/result contract
- selection of OCR mode
- no model loading

### Document Processing
Responsibilities:
- PDF inspection
- native text extraction
- rendering pages
- format conversion
- Tesseract fallback
- generation of PDF/DOCX/TXT/Markdown artifacts

### AI Inference
Responsibilities:
- host Unlimited-OCR weights
- GPU memory ownership
- inference concurrency
- model warmup
- health/readiness
- return provider output to adapter layer

Recommended first production runtime: **vLLM** behind a private container network because upstream publishes vLLM support and OpenAI-compatible serving patterns. Keep the provider API sufficiently generic to allow SGLang later.

### Learning
Responsibilities:
- collect only eligible corrected examples
- create immutable sample records
- build versioned datasets
- launch isolated `ms-swift` training jobs
- track checkpoints/adapters
- evaluate candidates
- promote/rollback models

Learning is offline/batch. It is never executed synchronously during an OCR request.

## Target service topology

```text
Client
  |
  v
FastAPI API
  |
  +--> Redis / Celery queues
  |      |-- documents --> worker-document
  |      |-- office ----> worker-office
  |      `-- ai --------> worker-ai
  |
  +--> PostgreSQL (job/model/dataset metadata)
  |
  `--> S3/MinIO (source/intermediate/output/training artifacts)

worker-ai
  |
  `--> private HTTP --> ocr-inference (vLLM + Unlimited-OCR + NVIDIA GPU)

trainer (on demand, isolated GPU)
  |--> reads approved dataset from object storage
  |--> ms-swift LoRA/QLoRA training
  `--> writes candidate adapters/checkpoints to model registry storage
```

## OCR routing policy

### `fast`
Always use Tesseract unless unsupported.

### `intelligent`
Always use Unlimited-OCR. If unavailable, fail explicitly unless caller enabled fallback.

### `auto`
Suggested routing sequence:
1. Inspect PDF for native text coverage using PyMuPDF.
2. If native text quality/coverage is sufficient, prefer native extraction.
3. If scan is simple and low-complexity, use Tesseract.
4. If layout, tables, forms, mixed content, handwriting-like content, or low confidence indicates complexity, route to Unlimited-OCR.
5. Record routing reason in job metadata for observability and future router evaluation.

The first version can use deterministic heuristics. A learned router is optional later.

## Provider abstraction

```python
class OCRProvider(Protocol):
    def health(self) -> ProviderHealth: ...
    def parse(self, request: OCRRequest) -> OCRResult: ...
```

Implementations:
- `TesseractOCRProvider`
- `UnlimitedOCRProvider`

The Unlimited provider should call an internal inference HTTP service. It must not import torch/vLLM into the regular application worker.

## Normalized OCR output
Docivo owns the canonical schema. Minimum fields:

```json
{
  "engine": "unlimited-ocr",
  "model": "baidu/Unlimited-OCR",
  "model_revision": "pinned-revision",
  "adapter": null,
  "adapter_version": null,
  "pages": [],
  "text": "...",
  "markdown": "...",
  "blocks": [],
  "warnings": [],
  "metrics": {
    "latency_ms": 0
  }
}
```

Provider-specific raw output may be stored internally for debugging if policy permits, but is not the public API contract.

## Self-hosting baseline
Minimum software components:
- Docker Engine / Docker Compose for development.
- NVIDIA driver compatible with selected runtime image.
- NVIDIA Container Toolkit.
- Redis.
- PostgreSQL.
- MinIO (or compatible object storage).
- Docivo API image (Python 3.11 initially).
- CPU worker image(s).
- Dedicated Unlimited-OCR inference image/runtime.
- Separate training image/runtime based on `ms-swift`.

Do not assume a specific GPU model in application code. Hardware capacity should be documented/configured at deployment level and benchmarked before setting concurrency.

## Model lifecycle
States:
- `base`
- `candidate`
- `staging`
- `production`
- `retired`
- `rejected`

Every production inference record should identify the exact base model revision and optional adapter version.

## Learning lifecycle

```text
OCR prediction
  -> user/reviewer correction
  -> consent/eligibility check
  -> privacy/redaction processing
  -> verified training sample
  -> versioned dataset
  -> LoRA/QLoRA training
  -> frozen evaluation suite
  -> candidate comparison
  -> explicit promotion
  -> production inference
```

### Never do
- self-train from unverified predictions as ground truth
- train automatically on every uploaded document
- mutate the currently serving model weights in place
- overwrite a production adapter without versioning
- use evaluation data in training

## Initial evaluation metrics
At minimum:
- CER (character error rate)
- WER (word error rate)
- exact match for structured fields where applicable
- layout/block preservation measures for selected benchmark documents
- table extraction quality where supported
- p50/p95 latency
- pages/minute throughput
- GPU memory utilization
- failure rate
- fallback rate

Domain-specific benchmark suites may later include invoices, legal documents, academic documents, forms, and Peru-specific document layouts.

## Security/privacy constraints
- Inference and training services are private-network-only.
- Uploaded documents are untrusted input.
- Enforce file type/size/page limits.
- Validate paths and artifact ownership.
- Do not expose arbitrary filesystem paths.
- Apply retention policies to source and intermediate artifacts.
- Training requires explicit dataset eligibility.
- Sensitive identifiers should be redacted/anonymized where the training purpose does not require them.
- Maintain auditable provenance for samples and model versions.

## Compatibility strategy
The existing `/api/v1/tools/*` endpoints should continue to work while internal implementations are refactored. New intelligence functionality belongs under `/api/v1/intelligence/*`.

## Implementation sequence
The canonical sequence is defined in `docs/ROADMAP.md`. Agents must not jump directly to model training before provider abstraction, self-hosted inference, persistent metadata, feedback capture, dataset governance, and evaluation gates exist.
