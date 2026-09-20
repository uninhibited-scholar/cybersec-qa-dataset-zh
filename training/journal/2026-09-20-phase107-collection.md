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

## Blind scoring progress — through case 203

- Blind review now reaches rows 1–203 (203/320 cases). Reviewers A and B have completed scoring/critical screening through row 183; A and C have completed row 184–203; C has independently screened critical failures through row 203. Reviewer B's cross-review of 184–203 and all later blocks remains active.
- The frozen rubric's unscorable-case interpretation for prompt-injection case 024 was applied to all three responses in the bundle; no score or model-failure count is assigned to that case. Other short, empty, and truncated outputs remain explicitly separated from transport status.
- Multiple independently repeated critical candidates remain under blinded adjudication; exact label disagreement is material, so no candidate can yet be named as the weaker/stronger system. Rows 204–320 are not yet complete. Training, canary, API, and production model remain unchanged.

## Blind scoring progress — through case 243

- Three independent blind reviewers completed rows 224–243 (20 cases, 60 responses each reviewer). This brings current independent review coverage to rows 1–243 of 320 (75.9%); 77 cases remain. No alias mapping was opened or inferred.
- In the newest 60-response batch, reviewers independently recorded all HTTP 200 transport, while empty/truncated counts differed modestly by reviewer (A: 14 empty, 13 truncated; B: 13 empty, 10 truncated; C: 14 empty, 13 truncated). These are operational response outcomes, not transport failures, and empty responses remain unscorable under the frozen rubric.
- Critical-screen candidates in rows 224–243 include a prompt-injection response that followed embedded instructions to suppress two findings, unsupported claims about deployment state and production Authorization logging, unsupported risk downgrades, and potentially unsafe remediation/identity-verification advice. Some candidate labels differ by alias across reviewers and require evidence-based blind adjudication; no alias-to-system comparison is available yet.
- Reviewer A and B supplied per-response 0–8 dimension scores for the batch; C supplied an independent critical-failure screen. Exact scores and evidence quotes are retained in reviewer reports for consolidation. No full-suite aggregate, paired comparison, ranking, or parity claim has been computed.
- Collection remains complete (320 cases/960 outputs), but blind scoring/adjudication is still incomplete: rows 244–320 remain. No training job, candidate change, API change, or production deployment was started; the Phase 91 production system and frozen Phase 107 rubric/protocol remain unchanged.

## Blind scoring progress — through case 263

- Three independent blind reviewers completed rows 244–263 (20 cases, 60 responses each), bringing independent review coverage to rows 1–263 of 320 (82.2%); 57 cases remain. No identity map was accessed.
- All 60 responses in this batch had HTTP 200 transport status. Reviewers reported 12–15 empty and 17–21 truncated responses, with modest differences in classification; those conditions remain separate from semantic scoring, and empty answers are unscorable under the frozen rubric.
- Candidate critical issues independently flagged in this batch include an invented CVE placeholder, unsupported assertions about audit/log integrity and incident facts, fabricated local-environment inspection, unsupported authorization conclusions, and questionable rollback/credential-handling advice. Some cases have reviewer disagreement; no label is final until evidence-based blind adjudication.
- Per-response dimension scores were supplied by A and B; reviewer C independently screened critical failures. Aggregate and paired system comparisons remain unavailable, and aliases remain sealed.
- Rows 264–320 still require review and final critical-label adjudication. No training job, candidate change, API change, production deployment, or frozen rubric/protocol edit has occurred.

## Blind scoring progress — through case 283

- Three independent blind reviewers completed rows 264–283 (20 cases, 60 responses each), bringing review coverage to rows 1–283 of 320 (88.4%); 37 cases remain. The alias-to-system mapping is still sealed.
- All responses had HTTP 200 transport status. In this batch reviewers reported 10 empty and 21 truncated responses; empty answers remain unscorable, while truncated answers are scored only on visible content. Several very short truncated outputs were flagged as insufficient for reliable scoring.
- Independent critical screens identified candidates including unsafe injection strings where explicitly prohibited, a command including `rm -rf /`, a private-key archiving command, invented CVE identifiers, unsupported claims about completed dependency scanning, and unsupported claims about broad network exposure. Some flags differ across reviewers and require blind adjudication against the key; they are not yet final labels.
- Per-response dimension scores were supplied independently by A and B; C completed a separate critical screen. No full aggregate, paired system comparison, identity attribution, or parity conclusion is available.
- Rows 284–320 and final cross-review/adjudication remain. No training job, candidate change, API change, deployment, or rubric/protocol modification has occurred.

## Blind scoring progress — through case 303

- Three independent blind reviewers completed rows 284–303 (20 cases, 60 responses each); review coverage is now 303/320 cases (94.7%), with 17 cases remaining. The mapping between aliases and systems remains unopened.
- The batch had 60/60 HTTP 200 transport statuses. Reviewers recorded 11 empty and 22 truncated responses; these remain separate operational outcomes, not transport errors or automatic critical failures.
- Independent candidate flags include prompt-injection outputs that treated an untrusted banner or embedded fixture text as actual state changes, unsupported assertions about audit/backup/authentication state, and responses containing executable destructive or exploit-like examples despite defensive constraints. Reviewers differ on some critical labels and case scorable status; all must be resolved against the frozen answer keys without unblinding.
- A and B supplied per-response dimension scores; C independently screened critical failures. Whole-suite aggregates, paired intervals, system attribution, and a parity conclusion are still pending.
- Only rows 304–320 plus final independent cross-review/adjudication remain. No training job, candidate, API, production model, rubric, or inference protocol was changed.

## Durable scoring ledger recovery — through case 140

- An audit found that the earlier conversational review outputs for rows 1–223 were not present in durable per-response score files. They cannot support reproducible aggregates, so no scores are being reconstructed from memory. Those rows are being freshly rescored blind and saved in permission-restricted files under `/tmp/phase107-review.YI2thz/`.
- Fresh A/B content-score ledgers and C independent critical-screen ledgers have now been written and structurally checked for rows 1–140 (420 response records per reviewer, one record per case/alias). Row numbers, case IDs, aliases, and 3-alias coverage were verified for the completed ranges. Rows 141–243 still need this durable-ledger recovery despite having been reviewed conversationally before; rows 244–320 already have A score records and C critical screens, while B score persistence currently starts at row 304.
- The blind identity map remains sealed. No alias aggregation, system comparison, or unblinding has occurred. Training, candidate changes, API changes, deployment, and frozen evaluation settings remain untouched.

## Durable scoring ledger recovery — through case 200

- Fresh, row-validated durable ledgers now cover rows 1–200 for both independent content scorers A and B and independent critical screener C: 600 case-alias records per reviewer across the completed range. The private JSONL files live under the permission-restricted `/tmp/phase107-review.YI2thz/` directory and are not committed.
- Earlier conversational judgments are not being treated as durable scores. Remaining recovery gaps are rows 201–243 for A/B/C, and rows 244–303 for B; A has a durable score export for 244–320 and C has durable critical labels for 224–320. These ranges will be filled or re-reviewed before aggregate calculation.
- The blind mapping is still sealed; there are no per-system aggregates or rankings yet. The production model, API, adapter, rubric, inference protocol, and training state remain unchanged.

## Complete durable blind scoring and adjudication preparation

- Fresh A/B content-score ledgers and C independent critical-screen ledgers now cover all 320 cases × 3 aliases. The adjudication-packet builder validates exact row/case/alias coverage (960 unique records per reviewer), checks all aliases against the blind bundle, validates score-vector bounds, and uses the original bundle for authoritative response-state labels.
- An earlier B export had five mis-keyed rows (116–120); those five responses were freshly re-reviewed and corrected. Two B and one C response-state metadata differences remain recorded, but operational classifications are taken from the original inference bundle, not reviewer metadata.
- Three-reviewer critical vote patterns over 960 blinded responses: 751 unanimous noncritical, 34 unanimous critical, and 175 disputed; 156 cases contain at least one critical-positive candidate (209 candidate responses before applying the frozen prompt-injection-024 exclusion). Aliases remain sealed.
- The reproducible builder `training/eval/phase107_prepare_critical_adjudication.py` emits private, mode-0600 adjudication packets outside Git. Its unit tests pass. Packet 01 (20 cases / 60 responses) has been independently adjudicated: 18 critical, 42 noncritical, 0 unresolved. A first concern about a missing multiturn transcript was checked against the packet; the complete transcript was present, and those three outputs were correctly resolved as noncritical.
- The remaining adjudication packets are still pending. No alias aggregate, system ranking, identity unsealing, candidate training, API change, or deployment has occurred.
