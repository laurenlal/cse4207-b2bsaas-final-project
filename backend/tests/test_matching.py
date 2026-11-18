from ingestion.matching import best_match, result_condition

PRODUCT = {"productId": "sony-wh1000xm5", "mustInclude": ["wh-1000xm5"], "minPrice": 150, "maxPrice": 500}


def r(title, source, price, **extra):
    return {"title": title, "source": source, "extracted_price": price, **extra}


RESULTS = [
    r("Sony WH-1000XM5 Wireless Noise Canceling Headphones", "Best Buy", 329.99),
    r("Sony WH1000XM5 Headphones - Black", "Best Buy", 349.99),
    r("Hard Case for Sony WH-1000XM5", "Best Buy", 19.99),
    r("Sony WH-1000XM5 Wireless Headphones", "Walmart - Seller", 299.00),
    r("Sony WH-1000XM5 (Renewed)", "Back Market", 228.00),
    r("Sony WH-1000XM5 Headphones", "eBay", 210.00, second_hand_condition="pre-owned"),
    r("Sony WH-1000XM4 Wireless Headphones", "Target", 248.00),
    r("Sony WH-1000XM5 Replacement Ear Pads", "Amazon.com", 24.99),
    r("Sony WH-1000XM5 Wireless Headphones", "Amazon.com", 9999.0),
]


def pick(retailer, condition):
    return best_match(RESULTS, PRODUCT, {"retailer": retailer, "condition": condition})


def test_cheapest_matching_result_wins_and_accessories_are_ignored():
    assert pick("Best Buy", "new")["extracted_price"] == 329.99


def test_retailer_name_prefix_match():
    assert pick("Walmart", "new")["extracted_price"] == 299.00


def test_conditions():
    assert pick("Back Market", "refurbished")["extracted_price"] == 228.00
    assert pick("eBay", "used")["extracted_price"] == 210.00
    assert pick("Back Market", "new") is None


def test_wrong_model_and_price_bounds():
    assert pick("Target", "new") is None       # XM4, not XM5
    assert pick("Amazon.com", "new") is None   # only ear pads and an out-of-range price


def test_result_condition():
    assert result_condition({"title": "Thing - Refurbished"}) == "refurbished"
    assert result_condition({"title": "Thing", "second_hand_condition": "used"}) == "used"
    assert result_condition({"title": "Thing (Open Box)"}) == "used"
    assert result_condition({"title": "Thing used to be great"}) == "used"  # known limitation
    assert result_condition({"title": "Thing"}) == "new"
