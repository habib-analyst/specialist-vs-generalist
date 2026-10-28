"""Local model runner: transformers + torch on CPU, greedy decoding.

Weights are loaded from a local directory only (downloaded beforehand with
curl — see README). No network calls, no APIs, no cost. This module is the
ONLY place a model is invoked; everything it returns is a real generation
from the loaded weights.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


class LocalModel:
    def __init__(self, model_dir: str | Path):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._torch = torch
        self.model_dir = str(model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_dir, dtype=torch.float32
        )
        self.model.eval()

    def generate(self, messages: list[dict], max_new_tokens: int) -> str:
        torch = self._torch
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                num_beams=1,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        new_tokens = out[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)


def model_file_hashes(model_dir: str | Path) -> dict[str, str]:
    """SHA-256 of the weight/config files, recorded with the results."""
    hashes = {}
    for name in ("model.safetensors", "config.json"):
        path = Path(model_dir) / name
        if path.exists():
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes
