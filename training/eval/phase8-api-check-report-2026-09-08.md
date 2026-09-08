# Direct API check (active Phase 5 route)

Five independent, non-streaming authenticated requests to Mac mini localhost
18765 /v1/chat/completions, model qwen-cyber-agent; executed over SSH. No browser
or Harness prompt. Temperature 0, max_tokens 400, no tools. No adapter changes.

| Case | HTTP | Seconds | Manual assessment |
| --- | --- | --- | --- |
| Arithmetic | 200 | 2.41 | Correct: 3×12−7=29, no repetition |
| Hearsay | 200 | 1.61 | Fail: `演出预约已取消，但缺乏确认回执。` upgrades prior claim to fact |
| Accepted status | 200 | 4.14 | Correctly says acceptance is not proof of completion |
| Translation | 200 | 1.27 | Correct, no extra format instructions |
| Combined three questions | 200 | 2.92 | All three answered correctly and concisely |

No empty content, repeated answers, or raw tool parameters in these five outputs.
This is a single small regression (4/5 by manual assessment), not a general pass
rate. Prompts explicitly request brevity and clarify total borrowing, unlike some
earlier comparisons. Cannot attribute differences solely to API middleware.
All usage counts are zero despite nonempty content: token accounting unavailable
or incorrect, not evidence of zero generation or a measured token throughput.

Remote raw report:
/Users/jiehan/cyber-agent/phase8-api-check-20260908-165207.jsonl
Reproduction script: phase8_api_check.py. Credentials are neither printed nor saved.
