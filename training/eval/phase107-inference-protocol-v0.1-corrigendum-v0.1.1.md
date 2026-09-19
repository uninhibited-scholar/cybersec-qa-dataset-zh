# Phase 107 inference protocol v0.1 — corrigendum v0.1.1

**Approved by the user on 2026-09-19.** This corrigendum changes only the reference-arm transcription of Phase 91's actual effective no-tool system prompt. The Phase 107 v0.2 case suite, rubric v0.1, all other inference settings, and the production service remain unchanged.

## Correction

The collector's prior prompt copy omitted the newline joining the worker's base prompt to its no-tools clause and included two literal Markdown backticks not present in the deployed prompt. Use the exact no-tool system content reconstructed from the deployed Phase 91 worker for both reference models.

- Phase 91 worker SHA-256: `a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb`
- Effective prompt length: 425 Unicode characters
- Effective prompt SHA-256: `6017e9aab198e717f3d61082e08e45ca6fd0afa2158f750c43e1966110efe57e`
- All other protocol settings remain those in `phase107-inference-protocol-v0.1.md`.

The collector reconstructs the prompt from the live worker source without executing it, then fails closed unless the worker hash, effective prompt, and pinned prompt hash all match. Thus prompt drift blocks inference rather than silently changing the comparison.

## Interpretation

This aligns the **input system-prompt text** across the deployed Phase 91 endpoint and two references. The comparison remains end-to-end, not a raw-weight comparison: Phase 91 retains its endpoint-side retry, evidence/tool guards, and post-processing, while reference models use their native templates. These known runtime asymmetries remain disclosed under protocol v0.1.
