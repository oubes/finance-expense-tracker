def score_chunk(text: str) -> float:
    length_score = min(len(text) / 500, 1.0)
    sentence_score = text.count(".") * 0.1
    return round(length_score + sentence_score, 3)