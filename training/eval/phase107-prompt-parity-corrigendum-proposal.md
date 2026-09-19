# Phase 107 prompt-parity corrigendum — proposal only

Status: **Not approved; do not apply or run the benchmark from this proposal.** The approved v0.1 inference protocol remains unchanged until the user explicitly approves this correction.

## Evidence

The collector's reference-arm `SYSTEM_PROMPT` is 426 Unicode characters (SHA-256 `8ece8f47d1fcdca21bdcc8174539ad29182bbaaaf3eb7b303d5536aaaf53ade5`). Read-only inspection of the deployed Phase 91 worker (`phase91_worker.py`, SHA-256 `a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb`) found its effective no-tool system content is composed from the worker's 362-character base string, a newline, and its 62-character no-tools clause: 425 Unicode characters (SHA-256 `6017e9aab198e717f3d61082e08e45ca6fd0afa2158f750c43e1966110efe57e`).

The difference is limited to the missing newline separator and two literal backticks present only in the collector's copy. This is enough to violate the frozen protocol's claim of identical effective system content.

## Proposed minimal correction

1. Replace only the collector reference `SYSTEM_PROMPT` constant with the exact 425-character effective no-tool system content from the deployed Phase 91 worker.
2. Publish a clearly versioned protocol corrigendum recording the effective prompt SHA-256 `6017e9aab198e717f3d61082e08e45ca6fd0afa2158f750c43e1966110efe57e` and noting that this corrects a transcription mismatch; keep all other v0.1 protocol settings and rubric v0.1 unchanged.
3. Add a preflight that reconstructs/reads the deployed worker's no-tool prompt and fails closed unless its hash equals the collector's reference prompt hash.
4. Re-run the same v0.2, 320-case benchmark only after approval. No model weights, production service, tools, dataset, answer key, scoring criteria, or permissions change.

## Approval requested

Approve or reject only the four corrections above. Until explicit approval is received, the previous pending job remains cancelled, no inference starts, and the production API remains untouched.
