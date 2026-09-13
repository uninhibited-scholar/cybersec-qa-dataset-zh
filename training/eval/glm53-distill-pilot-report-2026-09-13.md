# GLM-5.3 response-distillation pilot

The desktop ZCode configuration contains an enabled `builtin:bigmodel` provider
with a present credential and model entries for GLM-5.3 and GLM-5.3-Flash. The
selected coding-plan provider is separate and is not assumed to authorize bulk
training requests. This pilot used the explicitly configured BigModel API-key
provider and GLM-5.3.

One synthetic no-tool probe succeeded after disabling GLM thinking: the model
returned “不能，只能视为待确认状态。” A 12-question defensive pilot produced
9 usable candidate answers and 3 failed requests. The 9 usable rows were copied
to Mac mini at `/Users/jiehan/datasets/glm53-distill-pilot-20260913/`.

They are not mixed into Phase 10 and are not yet used for training. Prompts include
defensive analysis and some requests for exploit code; the teacher system prompt
converted those into explanations, detection and remediation. Manual review is
required before any row is promoted. Initial inspection found refusals for tcache
arbitrary-write code, kernel evasion details and an unverified CVE claim.

Security note: an initial experiment accidentally placed the API key in a local
curl process argument; that request was stopped immediately. Subsequent requests
used in-memory credentials and the key was never written to Git or output. Rotate
the key if other untrusted local users could inspect process listings.

Distillation decision: the endpoint and response format work, so response
distillation is feasible. Do not train on these rows until reviewed, deduplicated
against the clean corpus and placed in a teacher-quality split. Log model,
timestamp, prompt version and review decision for every row.
