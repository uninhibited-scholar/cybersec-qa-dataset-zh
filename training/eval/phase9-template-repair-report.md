# Official-template candidate repair, 2026-09-09

## Root findings

The original local model tokenizer has no chat_template. The phase3 wrapper
template concatenates message content without role delimiters. Consequently,
Phase8's messages dataset did NOT by itself establish proper ChatML training.
The earlier description of Phase8 as standard-chat training is corrected here.
Earlier apply_chat_template-based raw evaluation also used this wrapper: it
must not be described as a verified standard-ChatML benchmark.

## Candidate implementation

chat_worker_v2.py preserves caller roles, history and tool results using the
official Qwen3-4B template, with enable_thinking=False. It removes fixed Markdown
requirements and output rewriting in this isolated worker. Original files and
serving process remain unchanged. This candidate has NOT been deployed.

Official tokenizer configuration downloaded from:
https://huggingface.co/Qwen/Qwen3-4B/raw/main/tokenizer_config.json
SHA256: d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101
Remote dependency: ~/cyber-agent/qwen3-official-tokenizer-config.json.
Only its chat_template is applied; local tokenizer vocabulary is retained.

## Controlled results

Same original model directory, official template and greedy decoding; no API
guards. Compare adapter absent versus phase5-best120. Four cases, once each.

| Case | Bare local base | Phase5 adapter |
| --- | --- | --- |
| One word allow/block | `block` | `block` |
| JSON arithmetic | `{"answer": 31}` (format pass, math fail) | Same |
| Explain parameterized queries in two sentences | Substantive correct explanation, one sentence | Empty |
| Unverified cancellation claim | Correctly states it cannot verify | Empty |

Thus caller-format behavior can work with correct transport, but the adapter
still regresses two answers relative to the local bare base in this small test.
Both models fail arithmetic here; no claim of complete base quality or general
adapter failure rate is justified. Weight provenance/quantization, thinking mode,
and generation settings remain possible contributors needing controlled tests.

The first trial failed before generation because the missing template was
detected; raw errors retained in ~/cyber-agent/phase9-chat-control.jsonl.
Corrected runs use timestamped phase9-chat-control-*.jsonl and never overwrite.

## Decision

Do not replace the service or resume the existing raw-concatenation training
recipe. Preserve candidate repair and failures. Next run must validate the
actual serialized training tokens and compare a fresh adapter trained using
the same official template as inference, with preserved held-out basic tasks.
Four diagnostic cases are insufficient for deployment approval.
