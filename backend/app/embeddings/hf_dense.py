from __future__ import annotations

from functools import lru_cache

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from app.core.settings import settings


def _mean_pool(last_hidden: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    # last_hidden: [B, T, H], mask: [B, T]
    mask = attention_mask.unsqueeze(-1).type_as(last_hidden)
    summed = (last_hidden * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1)
    return summed / counts


@lru_cache(maxsize=1)
def _load() -> tuple[AutoTokenizer, AutoModel, torch.device]:
    device = torch.device(settings.embedding_device)
    tok = AutoTokenizer.from_pretrained(settings.embedding_model)
    model = AutoModel.from_pretrained(settings.embedding_model)
    model.eval()
    model.to(device)
    return tok, model, device


class HuggingFaceDenseEmbedder:
    """
    Dense embedding wrapper for HF checkpoints.

    Note: ColBERT checkpoints are typically used with late-interaction retrieval.
    For this MVP (Chroma dense vector store), we compute a pooled dense vector.
    """

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        tok, model, device = _load()
        out_vectors: list[list[float]] = []

        # Simple batching to avoid OOM on CPU.
        batch_size = 8
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = tok(
                batch,
                padding=True,
                truncation=True,
                max_length=settings.embedding_max_length,
                return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.no_grad():
                res = model(**enc)
                pooled = _mean_pool(res.last_hidden_state, enc["attention_mask"])
                # L2 normalize (helps cosine-like similarity even if store uses L2)
                pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
                vecs = pooled.detach().cpu().numpy().astype(np.float32)

            for v in vecs:
                out_vectors.append(v.tolist())

        return out_vectors


