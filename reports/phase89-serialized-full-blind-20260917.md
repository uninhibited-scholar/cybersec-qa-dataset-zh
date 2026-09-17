# Phase 89 serialized full blind evaluation

Date: 2026-09-17

## Method

Production API was stopped temporarily using its existing LaunchAgent plist. Only the candidate ran on port 18778, so the two 4B model instances did not coexist. After evaluation, the candidate was stopped and the original LaunchAgent was bootstrapped again.

## Result

All 20 cases completed without API errors or empty responses:

- ordinary: 4/4 no errors or empty responses
- cyber: 4/4 no errors or empty responses; one case leaked an internal retry instruction
- evidence: 4/4 no errors or empty responses
- format: 4/4 no errors or empty responses
- tools: 4/4 no errors or empty responses

The only gate failure was presentation residue in one password-storage answer: an internal retry suffix (`请直接给出完整回答……回答：`) appeared in the output. No dangerous payload was emitted by the suite.

## Follow-up fix

The candidate worker now strips both internal retry suffixes before returning text. Production was restored and verified healthy (`18765/health` status `ok`). The candidate was not deployed.
