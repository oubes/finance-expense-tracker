import re
from langchain_core.documents import Document

# --- Constants ---
TOC_THRESHOLD = 0.4
DEFAULT_TOC_KEYWORDS = [
    r"\btable of contents\b",
    r"\bcontents\b",
    r"\bbrief contents\b",
    r"\bdetailed contents\b",
    r"\blist of chapters\b",
    r"\bwhat's inside\b",
    r"\btable of exhibits\b",
    r"\bindex of titles\b",
    r"\boutline\b"
]

# --- Pre-compiled Regex Patterns ---
KEYWORDS_PATTERN = re.compile(r"(" + "|".join(DEFAULT_TOC_KEYWORDS) + r")", re.IGNORECASE)
DOTS_PATTERN = re.compile(r"\.{3,}")
PAGE_NUM_PATTERN = re.compile(r"\d{1,3}\s*$", re.MULTILINE)

# Scoring Weights
KEYWORD_SCORE_WEIGHT = 0.5
DOTS_DENSITY_WEIGHT = 0.3
PAGE_NUM_DENSITY_WEIGHT = 0.2

# Checks for TOC introductory phrases
def has_toc_keywords(text: str) -> bool:
    if not text:
        return False
    return bool(KEYWORDS_PATTERN.search(text))

# Calculates the ratio of lines containing TOC-style dots
def get_dots_density(text: str) -> float:
    if not text:
        return 0.0
    lines = [l for l in text.split('\n') if l.strip()]
    if not lines:
        return 0.0
    dot_lines = sum(1 for l in lines if DOTS_PATTERN.search(l))
    return dot_lines / len(lines)

# Calculates the ratio of lines ending in page numbers
def get_page_num_density(text: str) -> float:
    if not text:
        return 0.0
    lines = [l for l in text.split('\n') if l.strip()]
    if not lines:
        return 0.0
    page_lines = sum(1 for l in lines if PAGE_NUM_PATTERN.search(l))
    return page_lines / len(lines)

# Computes a weighted score based on feature density
def compute_toc_score(text: str) -> float:
    if not text:
        return 0.0
    
    score = 0.0
    if has_toc_keywords(text):
        score += KEYWORD_SCORE_WEIGHT

    # Using density ensures small chunks and large chunks are scored fairly
    score += get_dots_density(text) * DOTS_DENSITY_WEIGHT
    score += get_page_num_density(text) * PAGE_NUM_DENSITY_WEIGHT

    return min(score, 1.0)

# Classifies text as TOC using weighted density score
def is_toc(text: str, threshold: float = TOC_THRESHOLD) -> tuple[bool, float]:
    score = compute_toc_score(text)
    return score >= threshold, score

# Enriches document metadata with TOC classification metrics
def enrich_metadata(doc: Document, threshold: float = TOC_THRESHOLD) -> dict:
    text = doc.page_content
    toc_flag, toc_score = is_toc(text, threshold)

    new_metadata = doc.metadata.copy()
    new_metadata.update({
        "is_toc": toc_flag,
        "toc_score": round(toc_score, 2),
        "toc_threshold_used": threshold
    })
    
    return new_metadata