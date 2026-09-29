def decide(candidates: list[dict], config) -> str:
    if not candidates or candidates[0]["confidence"] < config.review_threshold:
        return "unmatched"
    best = candidates[0]
    if len(candidates) > 1 and best["confidence"] - candidates[1]["confidence"] <= config.ambiguity_margin:
        return "manual_review"
    if best["confidence"] >= config.auto_accept and best["reason"] != "title_only":
        return "matched"
    return "manual_review"
