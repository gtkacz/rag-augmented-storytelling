from __future__ import annotations

from dataclasses import dataclass

from sentence_transformers import SentenceTransformer

from app.core.settings import settings


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    dim: int


class HFDenseEmbedder:
    def __init__(self) -> None:
        # SentenceTransformer handles local caching + device placement.
        self._model = SentenceTransformer(settings.embedding_model, device=settings.embedding_device)

    @property
    def dim(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(vectors=[], dim=self.dim)

        vecs = self._model.encode(
            texts,
            batch_size=settings.embedding_batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        vectors = vecs.astype("float32").tolist()
        return EmbeddingResult(vectors=vectors, dim=int(vecs.shape[1]))

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text]).vectors[0]
