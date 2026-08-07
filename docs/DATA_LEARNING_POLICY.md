# Docivo OCR Data & Continuous-Learning Policy

## Principle
Processing a document with Docivo does **not** automatically authorize that document for model training.

Inference data and training data are separate data classes with separate retention and eligibility rules.

## Training eligibility states
Every potential sample must have an explicit state:
- `ineligible`: must never be used for training.
- `pending_review`: eligibility not yet resolved.
- `eligible`: may be included in an approved dataset subject to validation.
- `revoked`: previously eligible but removed from future dataset builds where technically/legally required.

Default state for ordinary user OCR uploads: **ineligible** unless the product/legal policy explicitly establishes a valid opt-in or another documented lawful/contractual source.

## Valuable learning sample
A high-quality supervised OCR sample should contain:
- source image/page reference
- exact model/base revision that generated prediction
- optional adapter/version
- original prediction
- corrected/verified target
- document/page metadata necessary for reproducibility
- reviewer/verification status
- eligibility/consent provenance
- redaction/anonymization status
- immutable checksums
- timestamps

A raw model prediction is not automatically ground truth.

## Prohibited learning behavior
- online weight mutation after each request
- self-training from unverified OCR output as truth
- silently training on customer documents
- training from samples with unknown provenance
- modifying an existing released adapter/checkpoint in place
- mixing benchmark/test samples into train data
- retaining sensitive artifacts indefinitely without a retention purpose

## Privacy processing
Before inclusion in a training dataset, evaluate whether sensitive or identifying data is necessary to the learning objective.

Where it is not necessary, support redaction/anonymization of fields such as:
- identity numbers
- addresses
- telephone/email details
- account/payment information
- signatures
- embedded secrets/credentials
- other personal or confidential fields

Redaction policy must be domain-aware: do not destroy the target feature if that feature is legitimately required for an approved OCR benchmark/training purpose.

## Dataset construction rules
Every dataset version must:
1. reference only eligible samples;
2. have an immutable manifest;
3. document source domains/languages/document types;
4. define train/validation/test membership;
5. run duplicate and leakage checks;
6. record the policy/filter version used;
7. be reproducible from stored manifests and artifact versions;
8. never silently change after release.

If data changes, create a new dataset version.

## Evaluation isolation
Benchmark/test sets are frozen and access-controlled logically so that training builders cannot include them accidentally.

Model promotion compares a candidate against the current production baseline on the same approved evaluation suite.

## Model lifecycle
Recommended states:
- `candidate`
- `staging`
- `production`
- `retired`
- `rejected`

Promotion requires evaluation evidence. Rollback must remain possible.

## Deletion/revocation
The implementation must eventually support propagating deletion/revocation requests through:
- pending training samples
- future dataset builds
- relevant source artifacts according to retention policy

Historical models already trained from previously lawful/eligible data require a separately defined model-unlearning/legal policy; do not falsely claim deletion from a historical trained model is automatic.

## Auditability
Persist enough metadata to answer:
- Which source examples were in dataset X version Y?
- Which dataset trained adapter/model version Z?
- Which base Unlimited-OCR revision was used?
- Which training configuration and ms-swift version were used?
- What evaluation report justified promotion?
- Which model version processed a given OCR job?

## Continuous-learning cadence
The architecture supports periodic or manually triggered improvement cycles. It intentionally does not prescribe an arbitrary sample count or schedule before real data volume and compute economics are known.

A learning cycle is:

```text
eligible verified corrections
 -> dataset candidate
 -> quality/privacy validation
 -> immutable dataset version
 -> LoRA/QLoRA training
 -> candidate model/adaptor
 -> evaluation
 -> staging/canary if appropriate
 -> explicit promotion
 -> monitoring
```

## Upstream/base-model policy
Treat the Baidu base model as an external immutable dependency:
- retain required MIT notices;
- pin exact revisions in released deployments;
- evaluate upstream upgrades like any other model change;
- do not silently pull `main/latest` into production.
