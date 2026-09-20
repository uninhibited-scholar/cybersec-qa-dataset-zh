# 2026-09-20 — Phase 107 v0.2 blind collection complete

## Collection outcome

- Slurm job `43800` ran the approved CPU-only reference collection on `a100-2` using the pinned llama.cpp runtime and the frozen Phase 107 protocol. The collector wrote `960/960` response records for 320 v0.2 cases and three sealed aliases per case; its terminal log includes `complete=960/960` and `reference_collection_completed=true`.
- After the collector reported completion, job `43800` was cancelled to stop the reference servers and release the allocation. The later Slurm `FAILED`/exit-6 status is the script's expected “reference server exited unexpectedly” path after explicit cancellation; it occurred after the collector's successful completion marker, not during collection. User job `43670` was not touched.
- No answer-key or identity-map material was loaded during inference. Production Phase 91 was queried read-only; no model, adapter, API, prompt, protocol, rubric, or deployment setting was changed.

## Integrity and blind packet

- The tracked `phase107_prepare_blind_review.py` validator completed successfully: `review_bundle_ready cases=320 responses=960; identities remain sealed`.
- It verified 320 unique case IDs, exactly three aliases per case, all 960 distinct `(case_id, alias)` pairs, category alignment, the frozen suite version/hash, frozen protocol settings, and pinned Phase 91 worker/effective-prompt hashes. It loads the answer keys only after coverage validation.
- The permission-restricted review bundle contains only randomized case presentation, prompts, key anchors, and responses under aliases; it omits run order and identity mapping. Local working copy: `/tmp/phase107-review.YI2thz/bundle/phase107-blind-review-bundle.jsonl` (directory 0700, files 0600). Raw responses and identity mapping remain outside Git on the cluster; do not commit either.
- Raw response SHA-256: `092cf5875adb534ab69722d694d2ff1341050840482ce45edbdfb5080702f711`. Run manifest SHA-256: `0c39bc438bc4d62564dea2403d6d2bb5a40757c1c13c3ae31a1c1d279fd9de79`. Suite SHA-256 remains `6d75567be1ec32e1599951e98776625e93b4cc1826a269ff8b4f59304306d982`.
- Across the 960 blinded records, the collector classified 450 as `ok`, 325 as `truncated`, and 185 as `empty`; all had HTTP 200 transport status. Finish reasons were 450 `stop` and 510 `length`. These operational outcomes must be reported separately from content quality and must not be attributed to any system until identities are opened after blind scoring/adjudication.

## Remaining gate

- No content scores, rankings, parity claim, or identity unsealing have been performed.
- Next: complete blind scoring per the frozen rubric, record case-level critical-failure labels with evidence quotes, obtain the required independent blind adjudication before opening identities, calculate per-stratum aggregates and paired uncertainty, and only then compare aliases to systems.
- The current packet is prepared for review but no candidate improvement, training run, canary, or production deployment is authorized by this collection result.

## Initial reviewer process note (not a final score)

- One prior calibration reviewer noticed it had read the calibration report while preparing and withdrew before scoring. The other was interrupted before providing an independent final review. Two newly tasked reviewers with no inherited conversation history were then asked to review the same blind packet.
- Both newly tasked reviewers could only complete a tiny initial subset in their first response: reviewer A covered 1 case (3 outputs); reviewer B covered 3 cases (9 outputs). These partial scores and candidate critical-failure labels are **not** a full evaluation and must not be extrapolated.
- The two reviewers disagreed on some preliminary per-answer quality scores and on whether several unsupported claims meet the frozen critical-failure threshold. This confirms the need for adjudication; do not merge their partial labels into a final ledger or unseal identities.
- No model identity has been inferred or released. Further blind review remains outstanding; the goal is not complete.

## Blind review progress — first 43 cases

- Two reviewers have now independently scored overlapping batches, with coverage through bundle rows 1–43 (43/320 cases, 129 responses) across their completed chunks. At least 36 cases have two independent quality-score passes; one reviewer has completed a critical-failure screen of its assigned outputs. A third reviewer independently screened rows 1–43 for critical failures without seeing the other judgments. Reviews of later batches are in progress.
- The partial critical ledger contains multiple candidate issues involving unsupported high-impact claims, fabricated tool/file/log verification, embedded untrusted instructions, and unsafe evidence handling. Reviewers disagreed on whether some borderline cases meet the rubric's critical threshold; those are not adjudicated yet.
- These are candidate findings only: no aggregate quality score or critical-failure rate is reported from the partial sample, and the sealed identity mapping has not been consulted. Do not associate an alias with Phase 91 or either reference, and do not use the partial observations to train, change prompts, or promote a version.
- Reviewed subset boundaries, individual score tables, and short evidence quotes are in the independent reviewer outputs for this task; the benchmark artifact remains read-only and private. Remaining 277 cases still require blinded review before a full comparison can be reported.

## Extended independent review — through case 83

- Two primary reviewers have now completed independent four-dimension scoring and critical-failure screening of bundle rows 1–83 (83/320 cases, 249 responses each reviewer). A third reviewer has independently screened critical failures through row 63 and is continuing.
- The first 83 cases include repeated critical candidates in prompt-injection handling, unsupported claims about authentication/current state, fabricated tool/file/log access, invented CVE/source references, and operationally unsafe examples. The reviewers do not fully agree on several borderline items or exact failure category; the rubric requires blind adjudication before these become final labels.
- No alias-to-system mapping has been read or inferred for reporting. No full aggregate, ranking, or parity conclusion is available yet. Empty/truncated outputs and transport success remain separate outcome fields, not silent quality-score substitutions.
- Independent review is continuing in 20-case blocks; later cases remain unreviewed. Do not use partial results to train or alter the frozen test/rubric.

## Blind scoring progress — through case 163

- Review coverage now reaches bundle rows 1–163 (163/320 cases). Reviewer A has supplied rubric scores and critical labels for these rows; reviewer B has independently scored/checked through row 143 and is cross-reviewing 144–163; reviewer C has independently screened critical failures through row 163. This provides independent content scores on the bulk of completed rows and at least two critical screens for rows completed by two reviewers.
- Multiple candidate critical failures have been independently identified across untrusted-instruction handling, fabricated tool/file/log access, unsupported security conclusions, invented identifiers, and unsafe operational/evidence-handling recommendations. Some labels/categories remain contested and must be adjudicated blind. These are preliminary aliases only; no system attribution or aggregate is released.
- Rows 164–320 remain unreviewed. Scoring outputs are still separately tracked in reviewer task results; private responses/keys remain outside Git. No model improvement or deployment decision has been made from partial evidence.

## Blind scoring progress — through case 183

- Blind content review has reached rows 1–183 (183/320 cases). Reviewers A and B have scored through row 163; reviewer C has independently scored through row 163 and screened critical labels. Rows 164–183 have been scored by A and C; B's independent cross-review of that batch is queued. All three reviewers are continuing in non-overlapping/overlapping 20-case blocks to preserve independent checks.
- Many outputs in reviewed batches are truncated or empty despite successful HTTP transport; these are being kept as separate outcome dimensions. Critical-failure candidates include repeated instruction-following failures on untrusted artifacts and fabricated evidence/tool state, alongside less clear borderline factual claims; only independently supported/adjudicated labels should enter the final ledger.
- The mapping from aliases to systems remains sealed. No aggregate, model ranking, parity statement, or training change is based on the partial review. Rows 184–320 remain to be reviewed and independent adjudication is incomplete.
