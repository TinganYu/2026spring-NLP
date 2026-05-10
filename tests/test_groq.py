import diary.groq as groq


class _FakeResponse:
    def __init__(self):
        self.status_code = 200
        self.text = ""

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": "本週情緒偏低，頭痛與焦慮有明顯關聯。"
                    }
                }
            ]
        }


class _FakeRequests:
    def __init__(self):
        self.calls = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _FakeResponse()


def test_summarize_health_trend_builds_prompt(monkeypatch):
    fake_requests = _FakeRequests()
    monkeypatch.setattr(groq, "requests", fake_requests)
    monkeypatch.setattr(groq, "_GROQ_API_KEY", "test-key")

    result = groq.summarize_health_trend(
        {
            "emotion_trend": [{"date": "2026-05-01", "emotion_label": "negative"}],
            "symptom_trend": [{"date": "2026-05-01", "symptom_or_sign": ["headache"]}],
        }
    )

    assert "本週情緒偏低" in result.summary
    assert fake_requests.calls[0]["url"].endswith("/chat/completions")
    assert fake_requests.calls[0]["json"]["model"] == groq._GROQ_MODEL
    assert fake_requests.calls[0]["json"]["messages"][1]["role"] == "user"
