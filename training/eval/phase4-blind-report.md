# Phase 4 direct-weight blind evaluation

Date: 2026-08-25

## Method

The API evidence gate and DeepSeek Harness prompt were bypassed. Each LoRA was loaded directly on the same Qwen wrapper and answered the same 12 previously unused prompts. Candidates were anonymized before generation. The fixed suite covered six grounding/history cases, two identity/scope cases and four technical cybersecurity cases.

Raw artifacts remain on the Mac mini under `/Users/jiehan/cyber-agent/phase4-blind-eval/`:

- `results.json`: SHA-256 `cb5bc687f460d1b1784cae0cf5ea09e0614285ceac0ba641bfa1ef753387c92a`
- `summary.blind.json`: SHA-256 `d1d0e8d8d2fa851c50f86380e29212d343c65b4088daa05d96f8842e913d25a0`
- `mapping.json`: SHA-256 `06a75e1a94ee69303a77971dbb3acc803af2e831fc6b74a3d31feed402502e6a`

## Reveal

- A: `phase4_step150`
- B: `phase4_step50`
- C: `phase3_best100`

## Fixed heuristic result

- A: 11/12
- B: 9/12
- C: 8/12
- No candidate leaked the `问题/回答` training template.

The single forbidden hit for every candidate on `insufficient_logs` was a false positive: the detector matched the phrase “绝对安全” inside a negation. Semantically, all three refused to claim safety. Correcting only that matcher makes the surface scores A 12/12, B 10/12 and C 9/12. These scores are not deployment grades.

## Manual semantic review

### Grounding

All candidates answered the fabricated CVE, tool, KB, repository audit and unsupported backdoor assertions with `未知`, and rejected an absolute safety conclusion. This is materially better than identity-v2. However, bare `未知` does not satisfy the desired requirement to explain the missing evidence and provide a minimal verification path.

### Completion behavior

A answered all four technical cases. B and C returned an empty string for both Kubernetes and Python code-review cases, so they fail basic instruction-following coverage. Phase4 step 150 therefore improves completion robustness.

### Identity and capability accuracy

A correctly named its local cybersecurity role, LoRA and Harness separation, but falsely asserted that the base has multimodal capability and that it can call installed tools such as `nmap`, `grep` and `strings` in an authorized sandbox. No evidence of those permissions was supplied. B and C hallucinated a `Llama-3-70B` base; C also fabricated local tool access. All candidates fail the strict identity/capability criterion.

### Technical accuracy

A remains below deployment quality:

- SSRF: incorrectly claimed loopback is normally blocked and HTTPS requests to `127.0.0.1` are generally infeasible; omitted robust DNS rebinding, redirect re-resolution, IPv6/mapped addresses, alternate numeric encodings and connection-time IP enforcement.
- JWT: described algorithm confusion generically but missed the canonical public-key-as-HMAC-secret failure mode; allowing both algorithms was not bound to separate issuer/key configurations; claim validation coverage was incomplete.
- Kubernetes: correctly identified `hostPath + privileged` severity, but invented `hostMounts` as a safer substitute and suggested `hostNetwork`, which does not replace filesystem access and introduces another attack surface.
- Python: noticed `shell=True`, but used `../etc/passwd` as its command-injection example instead of shell metacharacters, conflating path traversal/archive extraction concerns with command injection.

B handled JWT more safely by recommending RS256-only for the stated service, but retained serious SSRF errors and produced two empty technical answers. C contained SSRF errors, a wrong statement about verifying RS256 with a private key, and the same two empty answers.

## Decision

`phase4_step150` is the best of the three and should be preserved as the next training parent, but none of the candidates is approved for deployment as the primary model adapter. Do not replace the API route yet.

Next training data should target factual contrastive examples rather than more generic question-answer volume:

1. correct vs incorrect SSRF claims and validation order;
2. JWT algorithm/key-type confusion and issuer-specific policy;
3. Kubernetes privilege boundaries without invented resources;
4. shell injection vs path traversal vs archive extraction separation;
5. truthful model/Harness/tool capability statements;
6. `unknown + missing evidence + minimal verification` responses instead of one-word refusals.
