#!/usr/bin/env python3
"""Run one reproducible Qwen/LoRA/prompt ablation on Apple MLX."""

import argparse
import json

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_logits_processors, make_sampler


def worker_prompt(question: str) -> str:
    return "\n".join([
        "以下是外层 DeepSeek Harness 提供的会话上下文。工具说明只表示可能可用，不表示已经执行：",
        "",
        "你是运行在用户 Mac mini 上、通过 API 接入 DeepSeek Harness 的本地网安特化语言模型。"
        "严格区分模型、知识库和外层工具；不得虚构未接入、未执行或未返回结果的能力。",
        f"问题：{question}",
        "回答：",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--prompt-mode", choices=("native", "worker"), required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--max-tokens", type=int, default=400)
    args = parser.parse_args()

    kwargs = {"lazy": False}
    if args.adapter:
        kwargs["adapter_path"] = args.adapter
    model, tokenizer = load(args.model, **kwargs)

    if args.prompt_mode == "native":
        try:
            prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": args.question}],
                tokenize=False,
                add_generation_prompt=True,
            )
        except ValueError as exc:
            if "chat_template is not set" not in str(exc):
                raise
            # The locally converted Qwen tokenizer omitted chat_template.
            # Use Qwen's standard ChatML delimiters for a clean base-model test.
            prompt = (
                "<|im_start|>user\n" + args.question + "<|im_end|>\n"
                "<|im_start|>assistant\n"
            )
    else:
        prompt = worker_prompt(args.question)

    answer = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=args.max_tokens,
        sampler=make_sampler(temp=0.12, top_p=0.9),
        logits_processors=make_logits_processors(
            repetition_penalty=1.12,
            repetition_context_size=128,
            frequency_penalty=0.08,
            frequency_context_size=128,
        ),
        verbose=False,
    ).strip()
    print(json.dumps({
        "adapter": args.adapter or None,
        "prompt_mode": args.prompt_mode,
        "question": args.question,
        "answer": answer,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
