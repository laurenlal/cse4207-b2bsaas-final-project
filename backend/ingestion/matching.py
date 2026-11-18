"""Pick the SerpApi Google Shopping result that corresponds to one tracked listing.

A result matches a listing when it comes from the listing's retailer, is in the listing's
condition, has every product.mustInclude term and no excluded word in its title, and is
priced within product.minPrice..maxPrice. The cheapest match wins.
"""

import re

DEFAULT_EXCLUDE = ["case", "cover", "replacement", "cushion", "cushions", "ear pads", "earpads",
                   "ear tips", "protector", "charger", "cable", "strap", "skin", "stand", "mount",
                   "adapter", "decal", "sticker", "bundle", "for parts"]


def norm(text):
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _has_word(title, word):
    return re.search(rf"(?<![a-z0-9]){re.escape(word.lower())}(?![a-z0-9])", title) is not None


def result_condition(result):
    marker = (result.get("second_hand_condition") or "").lower()
    title = (result.get("title") or "").lower()
    if any(w in f"{marker} {title}" for w in ("refurbished", "renewed", "reconditioned")):
        return "refurbished"
    if marker or any(_has_word(title, w) for w in ("used", "pre-owned", "preowned", "open box")):
        return "used"
    return "new"


def matches(result, product, listing):
    source = norm(result.get("source"))
    if not source or not source.startswith(norm(listing["retailer"])):
        return False
    if result_condition(result) != listing["condition"]:
        return False
    title = (result.get("title") or "").lower()
    if not all(norm(t) in norm(title) for t in product.get("mustInclude", [])):
        return False
    if any(_has_word(title, w) for w in DEFAULT_EXCLUDE + product.get("mustExclude", [])):
        return False
    price = float(result["extracted_price"])
    return product.get("minPrice", 0) <= price <= product.get("maxPrice", float("inf"))


def best_match(results, product, listing):
    """Cheapest result that matches this listing, or None."""
    found = [r for r in results if matches(r, product, listing)]
    return min(found, key=lambda r: float(r["extracted_price"]), default=None)
