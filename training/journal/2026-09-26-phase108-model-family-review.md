# Phase108 model-family review (2026-09-26)

## Decision context

The Qwen family is the current Phase108 experimental lineage, not a proven
scientific winner. Do not treat the existing Qwen adapter or its compatibility
with the current pipeline as evidence that Qwen is the best base model for the
research goal. Keep the current candidate isolated and intact while considering
model-family challengers. A LoRA adapter is tied to its base architecture,
dimensions, tokenizer, and chat template; Phase108 adapters must not be attached
to GLM, Gemma, Mistral, or another Qwen size.

## Current cluster snapshot

Read-only SSH/Slurm inspection succeeded on `slurmc` as `zj225`.

- GPU-LARGE exposes one node with 2 x A100-40G and one node with 1 x A100-40G.
- GPU-MEDIUM exposes one 2 x 3g.20gb node and one 1 x RTX-3090 node.
- At inspection, the only user job was unrelated job `44506`, pending on GPU-LARGE
  for resources.
- `/data3` quota was 280G / 479G (58.5%), below the 95% stop threshold.

These facts make a two-GPU inference compatibility smoke technically plausible,
but do not prove that a model will fit, be schedulable, or perform well.

## Non-Qwen candidates from primary model sources

1. **GLM-4.7-Flash** — official card describes a 30B-A3B MoE, MIT license,
   Chinese and English support, and provides vLLM/SGLang serving guidance. The
   official serving example uses tensor parallel size 4 and says those runtimes
   currently require their main branches. This is the leading agent/harness
   challenger to investigate, but its 31B total parameter weights—not the 3B
   active parameters—drive residency. A 2 x A100-40G smoke may be possible with
   a compatible precision/runtime and short context; it is not yet validated.
   Sources: https://huggingface.co/zai-org/GLM-4.7-Flash and
   https://github.com/vllm-project/vllm/blob/main/docs/models/supported_models.md
2. **Gemma 3 12B IT** — official card reports multilingual support and 128K
   context. A practical single-GPU comparison candidate, with gated access and
   Google usage terms to account for. Source:
   https://huggingface.co/google/gemma-3-12b-it
3. **Mistral Small 3.1 24B Instruct** — official card reports 24 languages,
   128K context, and Apache-2.0. More expensive: BF16 weights alone are about
   48GB, so one 40GB GPU is not a safe full-precision target. Source:
   https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
4. **GLM-4-9B-Chat-HF** — smaller Chinese-capable comparison baseline. Its
   custom license is suitable for academic research under its terms; commercial
   use has additional registration/conditions. It is an older generation and
   should be treated as a baseline, not presumed stronger than current Qwen.
   Source: https://huggingface.co/zai-org/glm-4-9b-chat-hf

GLM-5.3-Flash is officially published as a 320B-total / 18B-active model. It is
not a realistic single-A100 or 3090 deployment target; its active parameter
count must not be mistaken for total model memory. Source:
https://huggingface.co/zai-org/GLM-5.3-Flash

## Recommended comparison sequence

1. Keep Qwen as a control lineage; do not promote or discard Phase108 based on
   this model-family review.
2. First run isolated, low-cost compatibility checks (weight load, tokenizer /
   chat-template behavior, short generation, peak VRAM, API protocol) for Gemma
   3 12B and GLM-4.7-Flash. Prefer GLM-4.7-Flash as the agentic challenger if a
   compatible multi-GPU allocation is actually granted; otherwise Gemma 3 12B
   is the lower-friction non-Qwen candidate.
3. Only after compatibility passes, benchmark raw bases under the same harness
   contract and a valid, independently reviewed cyber evaluation set. Then
   train separate adapters from each base using the same clean training split,
   while preserving each model's native tokenizer/template.
4. Separate base-model effects from harness/tool effects. Keep tool access,
   system-message content, evaluation rubric, and task cases fixed; normalize
   only the model-specific message serialization needed by each tokenizer.
5. No new download, training job, candidate selection, production API change,
   adapter replacement, or tool-permission change was made in this review.

Generic vendor benchmark claims are motivation for candidate selection only;
they are not evidence of cybersecurity-specialist performance. Current Phase108
behavioral blind-evaluation gates remain unresolved.

## Follow-up source check and corrected practical ranking (2026-09-26)

The earlier recommendation treated GLM-4.7-Flash too optimistically for the
currently documented two-A100 node, and did not compare Mistral Small 3.2's
explicit dual-GPU serving guidance. Qwen is not a required research choice.

- **First practical non-Qwen challenger: Mistral Small 3.2 24B Instruct.** Its
  official card says BF16/FP16 inference needs about 55 GB GPU memory and shows
  vLLM with `--tensor-parallel-size 2`. It is Apache-2.0 and supports 24
  languages, including Chinese; the vendor reports improved instruction
  following and function calling over 3.1. These are fit/feature reasons to
  test it, not evidence that it outperforms Qwen on our cyber tasks.
  Source: https://huggingface.co/mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Chinese/agent challenger, conditional on runtime and allocation: GLM-4.7-
  Flash.** The official card identifies it as 30B-A3B, MIT-licensed, Chinese
  capable, and 62.5 GB in the repository. Its current official vLLM example
  uses TP4 and nightly/main-branch software. Although parameter-file size alone
  does not mathematically rule out sharding across two 40-GB cards, the
  documented launch path is not yet verified on our two-card node. Treat it as
  a compatibility experiment only until an authorized allocation and smoke
  test demonstrate otherwise.
  Source: https://huggingface.co/zai-org/GLM-4.7-Flash
- **Cyber-specialized comparator: Foundation-Sec-8B-Reasoning.** Its official
  card describes an instruction-tuned security reasoning model, but lists
  English as its supported language and `other` for the license; inspect its
  NOTICE/license before adoption. It is useful as a specialist comparator, not
  automatically our Chinese production base.
  Source: https://huggingface.co/fdtn-ai/Foundation-Sec-8B-Reasoning
- **Research-transparency alternative: OLMo-3.1-32B-Instruct.** Apache-2.0 and
  detailed training releases are attractive for reproducibility, while the
  model card lists English. Lower priority for our Chinese-first study.
  Source: https://huggingface.co/allenai/Olmo-3.1-32B-Instruct

Operational decision: retain Qwen only as the existing control lineage; do not
start a new Qwen training run by inertia. When cluster access is available,
first compare raw Qwen and Mistral under the same unchanged Harness contract;
run GLM compatibility only if its serving stack can be tested without changing
production or evaluation policy. The Phase108 Qwen adapter cannot be transferred
to another family. Dataset, Harness, API contract, and evaluation infrastructure
can be reused, but each family needs its own clean adapter and provenance.

At this follow-up, an SSH attempt to `slurmc.ie.cuhk.edu.hk` failed at DNS
resolution, and a second read-only attempt to the last recorded controller IP
was closed by the host. No model download, Slurm job, production change, or
evaluation change was made. Cluster state must be rechecked after connectivity
returns; the previously logged quota/job snapshot is historical, not current.
