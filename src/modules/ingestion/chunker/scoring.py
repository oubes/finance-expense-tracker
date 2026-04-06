# ---- Standard Library ----
import re
import math
from collections import Counter
from src.core.config.settings import AppSettings

# ---- Scoring Weights ----
REPETITION_WEIGHT = 0.5
SENTENCE_FACTOR_WEIGHT = 0.3
LENGTH_FACTOR_WEIGHT = 0.2

COMBINE_ALPHA = 0.6
COMBINE_BETA = 0.4

SENTENCE_SCORE_DIVISOR = 5
WORD_LENGTH_NORMALIZER = 100

MAX_DOMAIN_BOOST = 0.2
DOMAIN_BOOST_MULTIPLIER = 3

SIGMOID_STEEPNESS = 4.0
SIGMOID_CENTER = 0.5

DEFAULT_DOMAIN_VOCAB = {
    "income", "expense", "budget", "debt", "saving",
    "investment", "interest", "credit", "loan",
    "financial", "money", "cash", "assets", "liabilities",
    "retirement", "tax", "salary"
}


class ChunkScorer:
    # ---- Init ----
    def __init__(self, *, settings: AppSettings):
        self.chunk_size = settings.ingestion.chunk_size
        self.length_score_divisor = self.chunk_size
        self.domain_vocab: set[str] = set(DEFAULT_DOMAIN_VOCAB)

    # ---- Build Domain Vocabulary ----
    def build_domain_vocab(self, corpus: list[str], *, top_k: int = 200) -> None:
        words: list[str] = []

        for text in corpus:
            words.extend(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))

        counter = Counter(words)
        self.domain_vocab = set([w for w, _ in counter.most_common(top_k)])

    # ---- Tokenize ----
    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    # ---- Length Score ----
    def _compute_length_score(self, text: str) -> float:
        return min(len(text) / self.length_score_divisor, 1.0)

    # ---- Sentence Count ----
    def _compute_sentence_count(self, text: str) -> int:
        return len([s for s in re.split(r"[.!?]+", text) if s.strip()])

    # ---- Sentence Score ----
    def _compute_sentence_score(self, sentence_count: int) -> float:
        return min(sentence_count / SENTENCE_SCORE_DIVISOR, 1.0)

    # ---- Word Stats ----
    def _compute_word_stats(self, words: list[str]) -> tuple[int, int]:
        return len(words), len(set(words))

    # ---- Repetition Ratio ----
    def _compute_repetition_ratio(self, words_count: int, unique_words_count: int) -> float:
        if words_count == 0:
            return 0.0
        return 1 - (unique_words_count / words_count)

    # ---- Alpha Ratio ----
    def _compute_alpha_ratio(self, text: str) -> float:
        if not text:
            return 0.0
        alpha = sum(c.isalpha() for c in text)
        return alpha / len(text)

    # ---- Domain Ratio ----
    def _compute_domain_vocab_ratio(self, words: list[str]) -> float:
        if not words:
            return 0.0
        hits = sum(1 for w in words if w in self.domain_vocab)
        return hits / len(words)

    # ---- Domain Boost ----
    def _compute_domain_boost(self, ratio: float) -> float:
        return min(
            ratio * DOMAIN_BOOST_MULTIPLIER * MAX_DOMAIN_BOOST,
            MAX_DOMAIN_BOOST
        )

    # ---- Penalty ----
    def _compute_penalty(self, text: str, words: list[str], sentence_count: int) -> float:
        words_count, unique_words_count = self._compute_word_stats(words)

        repetition_ratio = self._compute_repetition_ratio(words_count, unique_words_count)
        sentence_factor = min(sentence_count / SENTENCE_SCORE_DIVISOR, 1.0)
        length_factor = min(words_count / WORD_LENGTH_NORMALIZER, 1.0)
        alpha_ratio = self._compute_alpha_ratio(text)

        penalty = (
            REPETITION_WEIGHT * (1 - repetition_ratio) +
            SENTENCE_FACTOR_WEIGHT * sentence_factor +
            LENGTH_FACTOR_WEIGHT * length_factor +
            0.2 * alpha_ratio
        )

        return max(0.0, min(penalty, 1.0))

    # ---- Combine ----
    def _combine_scores(self, length_score: float, sentence_score: float) -> float:
        return (
            COMBINE_ALPHA * length_score +
            COMBINE_BETA * sentence_score
        )

    # ---- Sigmoid ----
    def _squash(self, x: float) -> float:
        return 1 / (1 + math.exp(-SIGMOID_STEEPNESS * (x - SIGMOID_CENTER)))

    # ---- Score Chunk ----
    def score(self, text: str, raw_text: str | None = None) -> float:
        sentence_source = raw_text if raw_text else text

        words = self._tokenize(text)

        length_score = self._compute_length_score(text)

        sentence_count = self._compute_sentence_count(sentence_source)
        sentence_score = self._compute_sentence_score(sentence_count)

        base_score = self._combine_scores(length_score, sentence_score)

        penalty = self._compute_penalty(text, words, sentence_count)

        domain_ratio = self._compute_domain_vocab_ratio(words)
        domain_boost = self._compute_domain_boost(domain_ratio)

        raw_score = base_score * penalty * (1 + domain_boost)

        final_score = self._squash(raw_score)

        return round(final_score, 3)