"""Local semantic ranking; never imported by production retrieval."""
import math
from importlib.metadata import version
from app.schemas.retrieval import RetrievedChunk

MODEL_ID = "cross-encoder/ms-marco-MiniLM-L6-v2"
MODEL_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"


class SemanticChunk(RetrievedChunk):
    semantic_score: float


class SemanticReranker:
    def __init__(self, scorer=None, *, revision=MODEL_REVISION, batch_size=16, max_length=512):
        if batch_size <= 0 or max_length <= 0:
            raise ValueError("batch_size and max_length must be positive")
        self.batch_size = batch_size
        self.max_length = max_length
        if scorer is None:
            import torch
            from sentence_transformers import CrossEncoder
            scorer = CrossEncoder(MODEL_ID, device="cpu", max_length=max_length,
                                  revision=revision, activation_fn=torch.nn.Identity(),
                                  model_kwargs={"torch_dtype": torch.float32})
        self.scorer = scorer

    def truncation_flags(self, question, candidates):
        tokenizer = self.scorer.tokenizer
        encoded = tokenizer([question] * len(candidates), [c.text for c in candidates],
                            truncation=False, padding=False)
        return [len(ids) > self.max_length for ids in encoded["input_ids"]]

    def configuration(self):
        return {"model_id": MODEL_ID,
                "model_revision": getattr(self.scorer.model.config, "_commit_hash", None),
                "sentence_transformers_version": version("sentence-transformers"),
                "transformers_version": version("transformers"), "torch_version": version("torch"),
                "device": "cpu", "dtype": "float32", "batch_size": self.batch_size,
                "max_token_length": self.max_length}

    def rerank(self, question, candidates, k=5):
        if k <= 0:
            raise ValueError("k must be positive")
        if not candidates:
            return []
        scores = self.scorer.predict([(question, c.text) for c in candidates],
                                     batch_size=self.batch_size, show_progress_bar=False,
                                     convert_to_numpy=True)
        if len(scores) != len(candidates):
            raise ValueError("Scorer returned a different number of scores than candidates")
        rows = []
        for candidate, score in zip(candidates, scores):
            score = float(score)
            if not math.isfinite(score):
                raise ValueError("Semantic scores must be finite")
            rows.append(SemanticChunk(**candidate.model_dump(), semantic_score=score))
        # Python's stable sort preserves original RRF order for equal scores.
        return sorted(rows, key=lambda c: c.semantic_score, reverse=True)[:k]
