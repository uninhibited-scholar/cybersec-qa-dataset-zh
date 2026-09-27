# Phase108 v1.8-rev2 blinded raw-weight collection

## Scope and guardrails

This run compares the frozen base, Phase108 parent adapter, and corrected-r2
candidate in one isolated Transformers/CUDA runtime. It is a blinded response
collection only: no automatic score, capability claim, candidate selection,
production deployment, or tool-permission change. It does not change the
Phase107 rubric or inference protocol, the production API/adapter, or any
candidate weights. Answer keys are not copied to the compute node or opened by
the collector. Raw answers and the alias map remain mode-0600 private outputs.

The reviewer-frozen Phase108 v1.8-rev2 suite is pinned by freeze-record SHA
`1dd603084fe3f026954ead8cb55004514b1c5b43a3b3219b0b10b0489ac0d5bf`, cases
SHA `c028b564d2273fc6779f248918511fa2bff0fe73abc4c7bb4ab6051ecc3b91c9`, and
answer-key SHA `f79828a550fb80cd84aba7faa593cd84a4f47e08ee8afc358957726de17a4015`.
The no-tool system prompt was compared byte-for-byte with the frozen Phase107
protocol; its SHA is `8ece8f47d1fcdca21bdcc8174539ad29182bbaaaf3eb7b303d5536aaaf53ade5`.

## Pinned model inputs

- Base config/index SHA: `260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650` /
  `5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4`.
- Base weight shard SHA values are embedded in the collector and are verified
  from inside the scheduled compute allocation before model loading.
- Parent adapter: `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`.
- Corrected-r2 final adapter: `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Candidate trained for 7,621 steps from the parent adapter; frozen validation
  on 1,089 rows reported loss 1.7062584871 vs parent 1.7362299831. This is
  loss/checkpoint-selection evidence only, not a user-visible capability claim.
- Candidate manifest SHA `e60ae88a3f491ed94b13f9e26ef0892e5986c838f69dff2fcbf8714185a29636`
  records 19,621 train rows, 7,621 steps, LR `5e-6`, rank 8, MLX scale 20,
  PEFT alpha/effective scale 160/20, and `test_split_read=false`.
- Train-only exact contamination scan: 19,621 training rows, 0 exact overlaps,
  0 parse errors/unrecognized rows; audit SHA
  `f9b9b8d8d3032dae0b6471da54cc86a076fd8c76b4107d5abdcc4ff4a5cf3c44`.
  Validation/test splits were not read by that scan. This is only an exact
  overlap result, not proof against semantic or pretraining contamination.

## Collection protocol

The runner pins all input hashes, uses the protocol's exact no-tool system
instruction, sends each sealed user/assistant message sequence unchanged, and
uses temperature 0.12, top-p 0.9, top-k disabled, a 700-token cap, and a
1.12 repetition penalty over the latest 128 generated tokens. Sampling seeds
are case-derived and shared across arms. Candidate and parent use the
training-declared effective adapter scale 20; no scale sweep or blind-set
parameter selection is performed. Qwen3 thinking text is excluded from the
stored final answer; an unclosed thinking segment is counted as no visible
answer, and tool-control markers are counted separately. Each case is a fresh
conversation. The three arm labels and per-arm case order are randomized.

Runtime/template parity with the Phase91 production endpoint is not claimed:
this is a same-runtime raw-weight comparison using the frozen dequantized base
and its pinned tokenizer template, not an end-to-end Harness comparison. The
collector saves raw final answers, but never prompts or keys, to a private
compute-side directory. Only hash-bound aggregate findings are intended for
Git after the job is verified.

## Pre-dispatch verification

- Collector: `training/scripts/phase108_blind_collection_v18r2.py`.
- SLURM wrapper: `training/slurm/phase108_blind_collection_v18r2.sbatch`.
- Unit tests cover recent-window repetition handling, hiding unclosed
  reasoning, tool-marker detection, and safe output-directory lifecycle; run
  in the cluster `coevo` environment before dispatch.
- Chosen resource: an idle `GPU-TITANX` compute node through SLURM; no model
  inference runs on the login node. Output path is unique per job ID and mode
  0700. The active general Qwen service job is not modified.
- Cluster copies matched local hashes (before the output-dir fix below): collector
  `8ce85906bd41c097ca9c8a2296bdb73f43ee2a468640a54be1506a66c5788c6e`, tests
  `f3003eaf0d64e0d7a33f4b57407af150acfa839e0c00eaba79598a22924d7161`, SLURM
  wrapper `45f45edd874d5c8b7fdbb27acf13787a26063a8f0fbc01e1e596d5dcc438c0ca`,
  and adapter loader `00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371`.
- Cluster-side `bash -n`, `py_compile`, and the three collector unit tests
  passed before scheduling; the tests exercised only synthetic tokens/tensors.

## Dispatch and results

The first three submissions (`44796`–`44798`) terminated during wrapper
preflight; no inference or result directory was created. The first two logs
were insufficiently diagnostic; job `44798` surfaced the incorrect local
parent-SHA pin described below. After correcting the pin, rerun the cluster
unit tests and hash checks, then submit under a new job ID. No model-quality
result exists yet.

Correction verified; the exact pinned inputs and three synthetic-token unit
tests passed on the cluster. SLURM job `44799` started on `titanv1` at
2026-09-27 02:18:40 HKT. All seven content/script hashes passed, but the job
then failed before model loading because the wrapper created the unique output
directory before invoking a collector that correctly refuses to reuse any
existing directory. No inference was performed and the failure is not model
behavior. The wrapper no longer pre-creates that directory; the collector
atomically creates it with mode 0700. A fourth unit test now covers private
directory creation and refusal to reuse a path. Updated hashes are collector
`9a1efefb3f02080e459ffbf6ec8f9052129b4595f0061e104ea6cc007f9d2a64`, tests
`47b1ecd859e14627801f7e7a7120005be9d2d8af946961a60df07b52c135c80b`, and
SLURM wrapper `9599873ebaaf53b44d2d850ff49170f2de3950c574f6d38a4864d966ddc4fe30`.
They need cluster-side re-verification before a fresh submission.

## Dispatch failures and corrected hash pin

Collection jobs `44796` and `44797` both failed before creating a run
directory; neither performed inference. The second attempt emitted only its
wrapper-start marker. Job `44798` then made the preflight error explicit: I
had transcribed the expected parent SHA incorrectly in the new collector and
SLURM wrapper. This was a local pin error, not a mismatch in the training
input or candidate artifact. The authoritative Phase108 training-start log
(`phase108-scale20-44306.log`, SHA-256
`12e3001df6c0b048f7c1e9af6b303da22c8feea81b7a2b4d2cf16dd1dfb950b9`) records
input path `phase108-step12000-20260920/0012000_adapters.safetensors` and SHA
`3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`. The
current source file, the candidate manifest's `input_mlx_adapter_sha256`, and
the training-start log all agree on that exact hash; its mtime precedes job
44306. The candidate's final adapter SHA and manifest remain unchanged. The
collector/wrapper pin is corrected to the verified value; the failed jobs
remain in SLURM accounting and their unique result directories are absent.

The historical candidate manifest does not include a training-script hash,
so it is not fully reproducible from that manifest alone. The run-start log
and source file do verify the source path/hash; the provenance gap is retained
as a limitation rather than silently repaired retroactively.

## Revalidation before fresh dispatch (2026-09-27)

The local working tree still has unrelated user changes and untracked Phase108
artifacts; this journal entry and the already-committed collector changes are
kept separate from them. Current local checks reconfirmed the collector, test,
and SLURM wrapper hashes listed above, and `bash -n` passed on the wrapper.
The local macOS Python 3.14 environment lacks PyTorch, so its unit-test run
could not import `torch`; this is an environment limitation, not a test result.
The updated four-test suite therefore still needs to run in the cluster's
`coevo` environment before a new SLURM submission.

Cluster access could not be re-established from this session: the configured
cluster hostname did not resolve, and the previously known internal address
accepted TCP but closed the SSH connection during key exchange, before account
authentication. No authoritative current SLURM queue/accounting state was
obtained. No files were synchronized and no job was submitted in this check;
the next action is to restore the laptop's campus VPN/DNS path, then verify
cluster-side hashes/tests and queue state before submitting one fresh run.

A second local network inspection found Tailscale connected and the
GlobalProtect app process present, but the active DNS resolver list contains
no CUHK resolver and the cluster hostname still does not resolve. A route to
the known cluster subnet exists through a tunnel interface, yet SSH to the
known internal address is still closed during key exchange. These observations
do not establish a healthy campus VPN/SSH session; no authentication or
SLURM command ran. PanGPS produced no matching recent system-log records.

## Campus VPN restored and fresh blind collection dispatched

The GlobalProtect UI was inspected directly and showed “disconnected” with the
CUHK portal selected. After using the user's established campus-VPN workflow,
the UI showed “connected” to gateway `IENet_GW`; cluster DNS and SSH then
worked. No credentials were read or handled.

Before dispatch, the stale remote copies were confirmed to match the earlier
committed versions, and prior jobs `44796`–`44799` were confirmed terminal
`FAILED` with no result directory other than the empty/private directory from
44799. The updated collector, four-test suite, adapter loader, and SLURM wrapper
were synchronized. Their remote hashes match the pinned local hashes; wrapper
`bash -n` passed. Current cluster status showed the unrelated Qwen API job
44601 still running on `a100-3`, `titanv1` idle, and disk usage 287G/479G.

Fresh job `44803` was submitted to `GPU-TITANX` and started on `titanv1`. Its
log confirms all seven content/script hashes, all four cluster unit tests
passing, and creation of a private mode-0700 output directory. The collector
is now performing model inference. One randomized blinded arm has completed
320/320 responses; its aggregate reports 298 empty answers and the private
response file is mode 0600. This is recorded only as a blinded diagnostic
signal: the identity map and keys have not been opened, and no model is named
or selected from this partial observation. A second arm is in progress. A
quiet five-minute heartbeat monitors job 44803; production API/adapters,
candidate weights, protocol, rubric, and permissions remain unchanged.

## Candidate training-source audit follow-up

Read-only Slurm accounting confirms training job `44306` completed with exit
0 on `a100-1` in 1:01:25, and its `SubmitLine` identifies
`sbatch data/training/slurm/phase108_cuda_scale_corrected.sbatch`. The
training-start log records the source adapter hash, train-row count, optimizer
settings, seed, and `test_split_read=false`; the final adapter hash matches
the pinned corrected-r2 artifact. The remote training runner currently has
SHA-256 `e69ea919024fe45cce9f39a1d6e38bec18282eb8a07c488f61f6aa8d9a5df728`
and exactly matches the runner in repository commit `6f35428` (2026-09-24
11:54:01 HKT), which predates the job start. The submitted batch-script path
exists in that same commit with SHA-256
`4fe393a7b33f3eaffec6d7f6974d46619f6316c3fc886194a2e4f62d8570eb3f`.
Commit `04c4388` changed that script at 11:55:28 HKT, after the job had
started, and the present remote copy was later modified again. This timeline
and the matching runner hash strongly identify the repository recipe used,
but Slurm's retained accounting stores only the submission path, not the
submitted script bytes or their hash. Thus the full training recipe is
recoverable from Git and the run log, while cryptographic attestation of the
exact batch-script bytes actually submitted remains unavailable; this
limitation is retained rather than overstated.

## Independent post-collection verifier prepared

Added `training/scripts/phase108_verify_blind_collection_v18r2.py` and its
synthetic-fixture tests. The verifier first requires authoritative `sacct`
`COMPLETED/0:0`, then checks the frozen suite and pinned model/script hashes,
private file modes, exactly 320 unique case IDs in each of aliases A/B/C,
response-file and per-answer hashes, response metadata, and aggregate counts.
It reports aggregate metadata by alias only, verifies that the identity map
exists and is private, but does not read or reveal the map or answer text. Four
synthetic tests pass locally, including rejection of a running job, a
corrupted arm, and deliberate proof that an invalid map is not parsed. These
tests do not inspect the active private outputs; the verifier has not yet been
run against job 44803.

One provenance limitation remains: the collector did not record the
identity-map SHA in its initial run manifest. The integrity verifier therefore
does not read or hash that map; after independent blind scoring is frozen, a
separate unblinding step can record its then-current SHA but cannot prove it is
byte-identical to its original creation state. The private 0700 output
directory/0600 map reduce exposure but are not a cryptographic
pre-commitment. Do not overstate arm attribution when reporting this run.

The verifier is paired with
`training/slurm/phase108_verify_blind_collection_v18r2.sbatch`, a 1-CPU/1-GB,
10-minute CPU-only post-job check on `GPU-TITANX` with no GPU requested, submitted
with an `afterany:44803` dependency. (The cluster `test` partition currently
has only 1 MB of configured memory on its one idle CPU, so it cannot run even
this small Python check.) The verifier job uses an available TitanX node's CPU
and memory only. It runs synthetic tests and then invokes
the verifier, which rejects any 44803 state other than `COMPLETED/0:0`. It
does not use a GPU, score, print answers, or reveal the map. This avoids doing
even small data-processing jobs on the login node. The verifier, test, and
batch-script hashes were checked against the local files after synchronization.
Slurm job `44837` is queued with the intended `afterany:44803` dependency and
requests only 1 CPU and 1 GB RAM; its report path is private under the run
directory. The verifier, test, and batch-script SHA-256 values on the cluster
match the local copies. The changes are committed locally; pushing the branch
to GitHub twice stalled without a ref update, and `ls-remote` confirms that
this branch is not yet present upstream. Do not claim GitHub backup until a
push is verified.

At this recheck, job 44803 is still running; alias C remains 320/320 and the
latest B progress marker is 80/320 (89 response records had been flushed).
No alias mapping was opened and no response text was
read for interpretation. The separate Qwen3-14B serving job 44601 remains
healthy per its in-job smoke results, but is not the Phase108 adapter and its
compute-node SSH tunnel from the laptop is still blocked by compute-node key
authorization. The verifier work does not change that service.

## Blind-review handoff compatibility check

The local Phase107 review-bundle builder is hard-bound to suite version
`phase107-v0.2`, its own response schema, and its prompt-parity fields; it is
not safe to point it directly at the v1.8-rev2 collection. The v1.8-rev2
answer-key file is present only in the ignored local evaluation directory; the
cluster suite directory currently contains the frozen cases and freeze record
but no answer-key file. No key contents were opened or transferred. After
44803 completes and 44837 verifies integrity, create a separate versioned
v1.8-rev2 blind-review packer that preserves the existing rubric/protocol,
validates all pinned hashes and all three 320-row arms, and leaves the identity
map sealed until reviewers freeze scores and critical-failure adjudications.

## v1.8-rev2 blinded review packer implemented

Added `training/eval/phase108_prepare_blind_review_v18r2.py`, a separate
versioned handoff adapter. It imports the existing integrity verifier from
`training/scripts`, requires its private verified report, rechecks the
collection's authoritative Slurm state and pinned cases/freeze/key/rubric/
protocol/corrigendum hashes, checks all 960 response records and digests,
shuffles case and response order, and writes answer-key-backed reviewer
materials only into a new mode-0700 directory with mode-0600 files outside the
Git repository. It never reads the sealed identity map or emits model labels;
the bundle remains explicitly unscored and ineligible for deployment.

Five synthetic tests pass locally: complete deterministic bundle construction,
rejection of an incomplete matrix, response-digest tampering, missing rubric
key field, and incorrect stratum counts. Python compilation also passes. No
real prompts, answer keys, or model responses were used by these tests. The
packer has not been run on the live collection: job 44803 was still RUNNING at
the latest poll (1:23 elapsed), with alias C complete and alias B at 80/320;
integrity job 44837 remained dependency-pending. Production, rubric/protocol,
permissions, and candidate artifacts remain unchanged.

The CPU-only post-integrity packer job wrapper is also prepared at
`training/slurm/phase108_prepare_blind_review_v18r2.sbatch`; `bash -n` passes.
It requires successful integrity job 44837, the private answer-key file, and
creates the blinded review bundle outside the repository with restrictive
permissions. The packer, verifier, their tests, the wrapper, and the pinned
rubric/protocol/corrigendum were staged in a new mode-0700 cluster directory;
remote SHA-256 values match local files. The answer key was deliberately not
transferred, and the packer job was not submitted while 44803/44837 remain
incomplete. Latest authoritative poll: 44803 RUNNING (1:31 elapsed), C=320,
B response file=118 rows, A not started; 44837 PENDING on dependency. No raw
responses or identity map were opened.

## Collection progress recheck

Later authoritative polls still show 44803 `RUNNING` on `titanv1` with exit
code not yet set; its Slurm time limit is 1 day. B has advanced to 121/320
flushed records, C remains 320/320, and A has not started because the runner
processes arms sequentially. 44837 remains `PENDING` on its declared dependency.
The delayed B arm is still advancing, so it was neither cancelled nor
restarted. No raw response text or identity mapping was read. The pre-staged
post-integrity packer has not been submitted and the answer key remains
unstaged remotely.

The packer wrapper now also hard-fails unless the response directory and
staging directory are mode 0700 and both the integrity report and staged
answer-key file are mode 0600. The revised wrapper passed local and remote
`bash -n`; its remote SHA-256 matches commit `b743988`. These checks are in
addition to the Python packer's frozen-artifact hash validation and do not
change the evaluation protocol.
