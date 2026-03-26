import hashlib
import math
import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_\+\#\./-]+")
CJK_PATTERN = re.compile(r"[一-鿿]{2,}")


def tokenize_text(text: str) -> list[str]:
    content = str(text or '')
    tokens = [match.group(0).lower() for match in TOKEN_PATTERN.finditer(content)]
    for segment in CJK_PATTERN.findall(content):
        tokens.append(segment)
        upper = min(len(segment) - 1, 6)
        for index in range(max(upper, 0)):
            tokens.append(segment[index:index + 2])
    return [token for token in tokens if token.strip() and len(token.strip()) > 1]


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    counter = Counter(tokenize_text(text))
    ranked = sorted(counter.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [token for token, _ in ranked[:limit]]


class BaseEmbeddingService:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    def batch_embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    @staticmethod
    def extract_keywords(text: str, limit: int = 12) -> list[str]:
        return extract_keywords(text, limit=limit)


class HashEmbeddingService(BaseEmbeddingService):
    def __init__(self, dimension: int = 256) -> None:
        self.dimension = max(32, dimension)

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = tokenize_text(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode('utf-8')).hexdigest()
            bucket = int(digest[:8], 16) % self.dimension
            sign = 1.0 if int(digest[8:16], 16) % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 12) / 24.0
            vector[bucket] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0:
            return vector
        return [round(value / norm, 6) for value in vector]
