import re
import math
from collections import Counter
from src.core.config.loader import load_settings

settings = load_settings()

# ---------- Constants ----------

REPETITION_WEIGHT = 0.5
SENTENCE_FACTOR_WEIGHT = 0.3
LENGTH_FACTOR_WEIGHT = 0.2

COMBINE_ALPHA = 0.6
COMBINE_BETA = 0.4

SENTENCE_SCORE_DIVISOR = 5
LENGTH_SCORE_DIVISOR = settings.rag.chunk_size
WORD_LENGTH_NORMALIZER = 100

# --- Domain Boost ---
MAX_DOMAIN_BOOST = 0.2
DOMAIN_BOOST_MULTIPLIER = 3

# --- Sigmoid ---
SIGMOID_STEEPNESS = 4.0
SIGMOID_CENTER = 0.5

# ---------- Domain Vocabulary (auto + fallback) ----------

DEFAULT_FINANCE_VOCAB = {
    "income", "expense", "budget", "debt", "saving",
    "investment", "interest", "credit", "loan",
    "financial", "money", "cash", "assets", "liabilities",
    "retirement", "tax", "salary"
}

DOMAIN_VOCAB = set(DEFAULT_FINANCE_VOCAB)


def build_domain_vocab(corpus: list[str], top_k: int = 200):
    """
    Build domain vocabulary dynamically from corpus
    """
    global DOMAIN_VOCAB

    words = []
    for text in corpus:
        words.extend(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))

    counter = Counter(words)
    most_common = [w for w, _ in counter.most_common(top_k)]

    DOMAIN_VOCAB = set(most_common)


# ---------- Helpers ----------

def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def _compute_length_score(text: str) -> float:
    return min(len(text) / LENGTH_SCORE_DIVISOR, 1.0)


def _compute_sentence_count(raw_text: str) -> int:
    return len([s for s in re.split(r'[.!?]+', raw_text) if s.strip()])


def _compute_sentence_score(sentence_count: int) -> float:
    return min(sentence_count / SENTENCE_SCORE_DIVISOR, 1.0)


def _compute_word_stats(words: list[str]):
    return len(words), len(set(words))


def _compute_repetition_ratio(words_count: int, unique_words_count: int) -> float:
    if words_count == 0:
        return 0.0
    return 1 - (unique_words_count / words_count)


def _compute_alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    alpha = sum(c.isalpha() for c in text)
    return alpha / len(text)


# ---------- Domain Boost ----------

def _compute_domain_vocab_ratio(words: list[str]) -> float:
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in DOMAIN_VOCAB)
    return hits / len(words)


def _compute_domain_boost(ratio: float) -> float:
    return min(ratio * DOMAIN_BOOST_MULTIPLIER * MAX_DOMAIN_BOOST, MAX_DOMAIN_BOOST)


# ---------- Penalty ----------

def _compute_penalty(text: str, words: list[str], sentence_count: int) -> float:
    words_count, unique_words_count = _compute_word_stats(words)

    repetition_ratio = _compute_repetition_ratio(words_count, unique_words_count)
    sentence_factor = min(sentence_count / SENTENCE_SCORE_DIVISOR, 1.0)
    length_factor = min(words_count / WORD_LENGTH_NORMALIZER, 1.0)
    alpha_ratio = _compute_alpha_ratio(text)

    penalty = (
        REPETITION_WEIGHT * (1 - repetition_ratio) +
        SENTENCE_FACTOR_WEIGHT * sentence_factor +
        LENGTH_FACTOR_WEIGHT * length_factor +
        0.2 * alpha_ratio
    )

    return max(0.0, min(penalty, 1.0))


# ---------- Combine ----------

def _combine_scores(length_score: float, sentence_score: float) -> float:
    return (COMBINE_ALPHA * length_score) + (COMBINE_BETA * sentence_score)


# ---------- Sigmoid ----------

def _squash(x: float) -> float:
    return 1 / (1 + math.exp(-SIGMOID_STEEPNESS * (x - SIGMOID_CENTER)))


# ---------- Main Function ----------

def score_chunk(text: str, raw_text: str | None = None) -> float:

    sentence_source = raw_text if raw_text else text

    # --- Tokenize once ---
    words = _tokenize(text)

    # --- Base scores ---
    length_score = _compute_length_score(text)

    sentence_count = _compute_sentence_count(sentence_source)
    sentence_score = _compute_sentence_score(sentence_count)

    base_score = _combine_scores(length_score, sentence_score)

    # --- Penalty ---
    penalty = _compute_penalty(text, words, sentence_count)

    # --- Domain Boost ---
    domain_ratio = _compute_domain_vocab_ratio(words)
    domain_boost = _compute_domain_boost(domain_ratio)

    # --- Raw score ---
    raw_score = base_score * penalty * (1 + domain_boost)

    # --- Squashed score ---
    final_score = _squash(raw_score)

    return round(final_score, 3)