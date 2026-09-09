# Fresh adapter with verified ChatML

Started from local bare Qwen3-4B, no resume adapter. Original files unchanged;
new model view Qwen3-4B-official-chatml-phase9 links weights and installs the
hash-verified official template with thinking disabled, matching inference.

Preflight processed all 48 training and 16 validation examples through MLX's
actual ChatDataset: generation prefix exactly equals masked training prefix,
responses fully present, maximum 73 tokens (<512), system/user roles preserved.
Test split unused. Data is the small neutral Phase8 pilot, NOT domain training;
shared templates limit validation independence.

Config phase9_fresh_chatml.yaml: 40 iterations, batch1/accum4, rank8/four layers,
LR1e-5, seed20260909, validation all16 every20. No claim of optimal LR.
PID25471 started via detached subprocess. Online API adapter unchanged.
Log: /Users/jiehan/cyber-agent/phase9-fresh-chatml-20260909.log
Output: /Users/jiehan/models/phase9-fresh-chatml-20260909
No deployment based only on loss; basic response comparison required.

## Completion and regression

All40 iterations completed. Validation loss 5.748 initial, 4.596 at20, 2.990
at40; final reported training loss2.546; peak2.630GB. These losses are not directly
comparable with old raw-concatenation runs. Model and old adapters preserved.

Repeated the four known diagnostic cases using phase9_chat_control.py with
CANDIDATE_LABEL=phase9 and CANDIDATE_ADAPTER pointing to the fresh output.
Both bare base and fresh candidate output `block` and valid JSON. Both give the
wrong arithmetic answer31. Fresh candidate now gives substantive parameterized
query explanation and correctly avoids confirming the unverified cancellation;
these two no longer return empty as Phase5 did. Two-sentence instruction was
not strictly met (one substantive sentence). This is a reused regression, not
an independent blind holdout, and does not prove domain improvement or no
overfitting. No serving adapter change; API health remained OK.

Next: broader unseen basic-task validation and investigate local base arithmetic
under controlled decoding before expanding to original domain dataset. Do not
claim this 48-example pilot is a completed specialist training run.
