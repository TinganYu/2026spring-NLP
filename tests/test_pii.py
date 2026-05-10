from shared.pii import detect_pii, has_pii, mask_pii, review_pii


def test_detect_pii_and_mask():
    text = "聯絡我 0912-345-678 或 user@example.com"
    review = review_pii(text)
    findings = detect_pii(text)

    assert review.needs_masking is True
    assert has_pii(text) is True
    assert any(item.category == "PhoneNumber" for item in findings)
    assert any(item.category == "Email" for item in findings)

    masked = mask_pii(text)
    assert "0912-345-678" not in masked
    assert "user@example.com" not in masked

