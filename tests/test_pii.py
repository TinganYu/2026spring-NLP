from shared.pii import review_pii


def test_review_pii():
    text = "聯絡我 0912-345-678 或 user@example.com"
    review = review_pii(text)

    # review is now a dict (TypedDict)
    assert review["needs_masking"] is True
    assert any(item["category"] == "PhoneNumber" for item in review["entities"])
    assert any(item["category"] == "Email" for item in review["entities"])
    assert review["redacted_text"] is not None
    assert "0912-345-678" not in review["redacted_text"]
    assert "user@example.com" not in review["redacted_text"]

