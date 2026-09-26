#!/usr/bin/env python3
"""Collect blinded Phase108 v1.8-rev2 raw-weight comparison responses.

The suite is read-only and answer keys are never opened. Raw final answers and
the alias map are private artifacts. This collector does not score responses
or authorize promotion. All arms share one base model, tokenizer, prompt
protocol, and sampler; only the LoRA weights differ.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random
import secrets
import statistics
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessor, LogitsProcessorList

from phase108_hf_adapter_smoke import LoRAProjection, attach_adapter


EXPECTED_CASES_SHA = "c028b564d2273fc6779f248918511fa2bff0fe73abc4c7bb4ab6051ecc3b91c9"
EXPECTED_PARENT_SHA = "3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036"
EXPECTED_CANDIDATE_SHA = "4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772"
EXPECTED_FREEZE_SHA = "1dd603084fe3f026954ead8cb55004514b1c5b43a3b3219b0b10b0489ac0d5bf"
EXPECTED_KEY_SHA = "f79828a550fb80cd84aba7faa593cd84a4f47e08ee8afc358957726de17a4015"
EXPECTED_BASE_CONFIG_SHA = "260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650"
EXPECTED_BASE_INDEX_SHA = "5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4"
EXPECTED_TEMPLATE_SHA = "9287fdda1d9257e0bdebaa2eac2db569a6cfc64d3b3ac1b812edd29f583bbc86"
EXPECTED_SYSTEM_PROMPT_SHA = "8ece8f47d1fcdca21bdcc8174539ad29182bbaaaf3eb7b303d5536aaaf53ade5"
EXPECTED_BASE_SHARDS = {
    "model-00001-of-00002.safetensors": "25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115",
    "model-00002-of-00002.safetensors": "a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d",
}
EXPECTED_ROWS = 320
MAX_NEW_TOKENS = 700
TEMPERATURE = 0.12
TOP_P = 0.9
REPETITION_PENALTY = 1.12
REPETITION_WINDOW = 128

# Exact no-tool system instruction frozen in phase107-inference-protocol-v0.1.md.
SYSTEM_PROMPT = (
    "你是运行在用户 Mac mini 上、通过 API 接入 DeepSeek Harness 的本地网安特化语言模型。严格区分模型、知识库和外层工具；不得虚构未接入、未执行或未返回结果的能力。正常回答用户提出的分析问题；证据不足时指出具体未知项，但不要用固定拒答替代可完成的文本分析。默认使用清晰 Markdown：先给结论，再按必要的小标题和要点展开；避免重复、空泛套话和过深层级。不要复述格式指令，也不要把长篇正文塞进工具参数。严禁编造上下文未提供的日志、指标、文件、函数、错误结构、百分比、测试次数或编号；没有证据的细节必须明确写为未知；普通知识、数学、历史和地理问题可以直接回答，不要套用网安拒答模板。结构化长答优先保证所有要求部分完整结束：每部分最多三个简洁要点，除非用户明确要求展开，总长度控制在约一千个中文字内。本轮没有向你提供工具。请只输出完整的纯文本 Markdown 回答，不得输出 `<tool_call>`、工具名或规划模式标记。"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class RecentWindowRepetitionPenalty(LogitsProcessor):
    def __init__(self, prompt_length: int, window: int, penalty: float):
        self.prompt_length = prompt_length
        self.window = window
        self.penalty = penalty

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        generated = input_ids[:, self.prompt_length:]
        if self.window:
            generated = generated[:, -self.window:]
        for row in range(scores.shape[0]):
            token_ids = torch.unique(generated[row])
            if token_ids.numel() == 0:
                continue
            selected = scores[row, token_ids]
            scores[row, token_ids] = torch.where(
                selected < 0, selected * self.penalty, selected / self.penalty
            )
        return scores


def clear_adapters(model) -> None:
    wrappers = [(name, module) for name, module in list(model.named_modules())
                if isinstance(module, LoRAProjection)]
    for name, wrapper in wrappers:
        parent_name, attr = name.rsplit(".", 1)
        setattr(model.get_submodule(parent_name), attr, wrapper.base)


def visible_answer(tokenizer, generated: torch.Tensor) -> tuple[str, bool, bool]:
    ids = generated.tolist()
    start_think = tokenizer.convert_tokens_to_ids("<think>")
    end_think = tokenizer.convert_tokens_to_ids("</think>")
    if isinstance(start_think, int) and start_think in ids:
        ends = [i for i, token in enumerate(ids) if token == end_think]
        if not ends:
            return "", False, True  # No user-visible final answer was produced.
        ids = ids[ends[-1] + 1:]
    marker_names = []
    for token_id in ids:
        token = tokenizer.convert_ids_to_tokens(token_id)
        lowered = str(token).lower()
        if "tool" in lowered or "function_call" in lowered:
            marker_names.append(lowered)
    text = tokenizer.decode(ids, skip_special_tokens=True).strip()
    return text, bool(marker_names), False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--parent-adapter", type=Path, required=True)
    parser.add_argument("--candidate-adapter", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--job-script", type=Path, required=True)
    parser.add_argument("--adapter-loader", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.output_dir.exists():
        raise SystemExit("output directory must be new; refusing overwrite")
    args.output_dir.mkdir(mode=0o700, parents=True)
    cases_raw = args.cases.read_bytes()
    freeze_raw = args.freeze.read_bytes()
    parent_sha = sha256_file(args.parent_adapter)
    candidate_sha = sha256_file(args.candidate_adapter)
    base_config_sha = sha256_file(args.base / "config.json")
    base_index_sha = sha256_file(args.base / "model.safetensors.index.json")
    template_sha = sha256_file(args.base / "chat_template.jinja")
    if hashlib.sha256(cases_raw).hexdigest() != EXPECTED_CASES_SHA:
        raise SystemExit("sealed cases SHA mismatch")
    if hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest() != EXPECTED_SYSTEM_PROMPT_SHA:
        raise SystemExit("system prompt provenance mismatch")
    if hashlib.sha256(freeze_raw).hexdigest() != EXPECTED_FREEZE_SHA:
        raise SystemExit("suite freeze SHA mismatch")
    freeze = json.loads(freeze_raw)
    if freeze.get("deployment_approval") is not False or freeze.get("production_change") is not False:
        raise SystemExit("freeze manifest is malformed or authorizes production changes")
    if freeze.get("cases_sha256") != EXPECTED_CASES_SHA or freeze.get("keys_sha256") != EXPECTED_KEY_SHA:
        raise SystemExit("freeze manifest does not pin the expected cases and keys")
    if (parent_sha, candidate_sha) != (EXPECTED_PARENT_SHA, EXPECTED_CANDIDATE_SHA):
        raise SystemExit("adapter SHA mismatch")
    if (base_config_sha, base_index_sha, template_sha) != (
        EXPECTED_BASE_CONFIG_SHA, EXPECTED_BASE_INDEX_SHA, EXPECTED_TEMPLATE_SHA
    ):
        raise SystemExit("base model/tokenizer provenance mismatch")
    base_index = json.loads((args.base / "model.safetensors.index.json").read_bytes())
    indexed_shards = set(base_index.get("weight_map", {}).values())
    if indexed_shards != set(EXPECTED_BASE_SHARDS):
        raise SystemExit("base shard inventory mismatch")
    for shard_name, expected_sha in EXPECTED_BASE_SHARDS.items():
        if sha256_file(args.base / shard_name) != expected_sha:
            raise SystemExit(f"base shard SHA mismatch: {shard_name}")
    cases = json.loads(cases_raw)
    if not isinstance(cases, list) or len(cases) != EXPECTED_ROWS:
        raise SystemExit("sealed suite row count mismatch")
    ids = [row.get("id") for row in cases]
    if len(set(ids)) != EXPECTED_ROWS:
        raise SystemExit("case IDs are not unique")
    for row in cases:
        messages = row.get("messages")
        if not isinstance(messages, list) or not messages:
            raise SystemExit("malformed sealed message sequence")
        if any(m.get("role") not in {"user", "assistant"} or not isinstance(m.get("content"), str)
               for m in messages if isinstance(m, dict)) or any(not isinstance(m, dict) for m in messages):
            raise SystemExit("malformed sealed message sequence")

    run_manifest = {
        "evaluation": "phase108_v1.8-rev2_blind_raw_weight_collection",
        "suite_freeze_sha256": hashlib.sha256(freeze_raw).hexdigest(),
        "cases_sha256": hashlib.sha256(cases_raw).hexdigest(),
        "answer_keys_sha256": EXPECTED_KEY_SHA,
        "candidate_sha256": candidate_sha,
        "parent_sha256": parent_sha,
        "collector_sha256": sha256_file(Path(__file__)),
        "job_script_sha256": sha256_file(args.job_script),
        "adapter_loader_sha256": sha256_file(args.adapter_loader),
        "base_config_sha256": base_config_sha,
        "base_index_sha256": base_index_sha,
        "base_weight_shards": EXPECTED_BASE_SHARDS,
        "chat_template_sha256": template_sha,
        "system_prompt_sha256": EXPECTED_SYSTEM_PROMPT_SHA,
        "inference": {"case_count": EXPECTED_ROWS, "max_new_tokens": MAX_NEW_TOKENS,
                      "temperature": TEMPERATURE, "top_p": TOP_P, "top_k": 0,
                      "repetition_penalty": REPETITION_PENALTY,
                      "repetition_window": REPETITION_WINDOW, "adapter_scale": 20.0,
                      "tools": [], "seed": "sha256(case_id) shared across arms"},
        "case_order": "independently shuffled per blinded arm",
        "arm_order": "randomized before inference",
        "blind": True, "scores": False, "promotion_eligible": False,
        "production_changed": False, "keys_opened": False,
    }
    manifest_path = args.output_dir / "run-manifest.json"
    manifest_path.write_text(json.dumps(run_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    manifest_path.chmod(0o600)

    alias_rng = secrets.SystemRandom()
    alias_labels = ["A", "B", "C"]
    alias_rng.shuffle(alias_labels)
    aliases = dict(zip(alias_labels, ["base", "parent", "candidate"]))
    alias_map = {v: k for k, v in aliases.items()}
    alias_path = args.output_dir / "identity-map.json"
    alias_path.write_text(json.dumps(alias_map, sort_keys=True) + "\n")
    alias_path.chmod(0o600)

    if not torch.cuda.is_available():
        raise SystemExit("evaluation must run inside a GPU Slurm allocation")
    capability = torch.cuda.get_device_capability(0)
    dtype = torch.bfloat16 if capability >= (8, 0) else torch.float16
    tokenizer = AutoTokenizer.from_pretrained(str(args.base), local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        str(args.base), torch_dtype=dtype, device_map="cuda:0", low_cpu_mem_usage=True,
        local_files_only=True, trust_remote_code=False,
    )
    model.eval()
    input_device = model.get_input_embeddings().weight.device
    runtime_path = args.output_dir / "runtime.json"
    runtime_path.write_text(json.dumps({
        "device": torch.cuda.get_device_name(0), "capability": capability,
        "dtype": str(dtype), "transformers": __import__("transformers").__version__,
        "torch": torch.__version__, "input_device": str(input_device),
    }, sort_keys=True) + "\n")
    runtime_path.chmod(0o600)
    arm_adapters = {"base": None, "parent": args.parent_adapter, "candidate": args.candidate_adapter}
    summaries = {}
    overall_start = time.monotonic()

    # Process one arm at a time to avoid changing model identity within a conversation.
    # Alias names and case ordering are randomized, and no key file is read.
    arm_order = ["base", "parent", "candidate"]
    random.SystemRandom().shuffle(arm_order)
    for arm in arm_order:
        clear_adapters(model)
        if arm_adapters[arm] is not None:
            attach_adapter(model, arm_adapters[arm], scale=20.0)
        alias = alias_map[arm]
        raw_path = args.output_dir / f"responses-{alias}.jsonl"
        raw_path.touch(mode=0o600, exist_ok=False)
        case_order = list(cases)
        random.SystemRandom().shuffle(case_order)
        counters = Counter()
        latencies = []
        with raw_path.open("w", encoding="utf-8") as output:
            for index, row in enumerate(case_order, 1):
                messages = [{"role": "system", "content": SYSTEM_PROMPT}, *row["messages"]]
                rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = tokenizer(rendered, return_tensors="pt").to(input_device)
                prompt_length = inputs["input_ids"].shape[1]
                # Same seed per case and arm for a paired, reproducible sampling condition.
                sample_seed = int.from_bytes(hashlib.sha256(row["id"].encode()).digest()[:8], "big") % (2**31)
                torch.manual_seed(sample_seed)
                torch.cuda.manual_seed_all(sample_seed)
                started = time.monotonic()
                with torch.inference_mode():
                    result = model.generate(
                        **inputs,
                        max_new_tokens=MAX_NEW_TOKENS,
                        do_sample=True,
                        temperature=TEMPERATURE,
                        top_p=TOP_P,
                        top_k=0,
                        repetition_penalty=1.0,
                        logits_processor=LogitsProcessorList([
                            RecentWindowRepetitionPenalty(prompt_length, REPETITION_WINDOW, REPETITION_PENALTY)
                        ]),
                    )
                elapsed = time.monotonic() - started
                new_tokens = result[0, prompt_length:]
                text, tool_marker, unclosed_thinking = visible_answer(tokenizer, new_tokens)
                eos = tokenizer.eos_token_id
                eos_ids = set(eos if isinstance(eos, list) else [eos]) if eos is not None else set()
                finish = "length" if len(new_tokens) >= MAX_NEW_TOKENS else (
                    "stop" if len(new_tokens) and int(new_tokens[-1]) in eos_ids else "other_stop"
                )
                record = {
                    "case_id": row["id"], "response": text,
                    "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "response_chars": len(text), "empty": not bool(text.strip()),
                    "generated_tokens": len(new_tokens), "finish_reason": finish,
                    "tool_marker": tool_marker, "unclosed_thinking": unclosed_thinking,
                    "latency_seconds": round(elapsed, 4),
                    "blind": True, "scored": False,
                }
                output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                output.flush()
                os.fsync(output.fileno())
                counters["empty"] += int(record["empty"])
                counters["tool_marker"] += int(tool_marker)
                counters["unclosed_thinking"] += int(unclosed_thinking)
                counters[f"finish:{finish}"] += 1
                latencies.append(elapsed)
                if index in {1, 40, 80, 120, 160, 200, 240, 280, 320}:
                    print(json.dumps({"alias": alias, "completed": index, "total": EXPECTED_ROWS}, sort_keys=True), flush=True)
        raw_sha = sha256_file(raw_path)
        summaries[alias] = {
            "responses_sha256": raw_sha,
            "cases": EXPECTED_ROWS,
            "empty_count": counters["empty"],
            "tool_marker_count": counters["tool_marker"],
            "unclosed_thinking_count": counters["unclosed_thinking"],
            "finish_reasons": dict(sorted((k.removeprefix("finish:"), v) for k, v in counters.items() if k.startswith("finish:"))),
            "median_latency_seconds": round(statistics.median(latencies), 4),
        }
        print(json.dumps({"alias": alias, "arm_complete": True, **summaries[alias]}, sort_keys=True), flush=True)

    result = {
        "evaluation": "phase108_v1.8-rev2_blind_raw_weight_collection",
        "suite_freeze_sha256": hashlib.sha256(freeze_raw).hexdigest(),
        "cases_sha256": hashlib.sha256(cases_raw).hexdigest(),
        "answer_keys_sha256": EXPECTED_KEY_SHA,
        "candidate_sha256": candidate_sha,
        "parent_sha256": parent_sha,
        "collector_sha256": sha256_file(Path(__file__)),
        "job_script_sha256": sha256_file(args.job_script),
        "adapter_loader_sha256": sha256_file(args.adapter_loader),
        "base_config_sha256": base_config_sha,
        "base_index_sha256": base_index_sha,
        "chat_template_sha256": template_sha,
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "inference": {"max_new_tokens": MAX_NEW_TOKENS, "temperature": TEMPERATURE,
                      "top_p": TOP_P, "top_k": 0, "repetition_penalty": REPETITION_PENALTY,
                      "repetition_window": REPETITION_WINDOW, "adapter_scale": 20.0,
                      "tools": [], "seed": "sha256(case_id) shared across arms"},
        "runtime": {"device": torch.cuda.get_device_name(0), "capability": capability, "dtype": str(dtype),
                    "transformers": __import__("transformers").__version__, "torch": torch.__version__},
        "summaries_by_blind_alias": summaries,
        "elapsed_seconds": round(time.monotonic() - overall_start, 3),
        "blind": True, "scores": False, "promotion_eligible": False,
        "production_changed": False, "keys_opened": False,
    }
    summary_path = args.output_dir / "aggregate.json"
    summary_path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    summary_path.chmod(0o600)
    print(json.dumps({"collection_complete": True, "summary_sha256": sha256_file(summary_path),
                      "elapsed_seconds": result["elapsed_seconds"], "blind": True, "scores": False}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
