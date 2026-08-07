# Docivo Backend Documentation

## AI / architecture context
- [`../AGENTS.md`](../AGENTS.md) — primary instructions for any AI coding agent.
- [`AI_CONTEXT.md`](AI_CONTEXT.md) — product/architecture context for self-hosted document intelligence.
- [`architecture/UNLIMITED_OCR_SELF_HOSTED.md`](architecture/UNLIMITED_OCR_SELF_HOSTED.md) — target deployment architecture for Baidu Unlimited-OCR.

## Planning
- [`ROADMAP.md`](ROADMAP.md) — dependency-ordered delivery phases.
- [`TASKS.md`](TASKS.md) — implementation checklist and task dependency map.
- [`SKILLS.md`](SKILLS.md) — competencies required by workstream/phase.

## Learning governance
- [`DATA_LEARNING_POLICY.md`](DATA_LEARNING_POLICY.md) — rules for feedback, training eligibility, datasets, model lifecycle, privacy and continuous learning.

## Direction summary
Docivo keeps existing CPU document-processing capabilities, preserves Tesseract as a fast/fallback OCR provider, and adds `baidu/Unlimited-OCR` as an isolated self-hosted GPU inference service. Verified corrections can later feed a controlled, versioned LoRA/QLoRA training pipeline through `ms-swift`; production model weights are never updated after every OCR request.
