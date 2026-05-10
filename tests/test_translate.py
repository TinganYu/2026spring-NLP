import shared.translate as translate


class _FakeTranslation:
    def __init__(self, text, to):
        self.text = text
        self.to = to


class _FakeDetectedLanguage:
    def __init__(self, language):
        self.language = language


class _FakeResponseItem:
    def __init__(self):
        self.detected_language = _FakeDetectedLanguage("zh-Hant")
        self.translations = [
            _FakeTranslation("Hello", "en"),
            _FakeTranslation("Hello (繁中)", "zh-Hant"),
        ]


class _FakeClient:
    def __init__(self):
        self.calls = []

    def translate(self, body, to_language, from_language=None):
        self.calls.append(
            {
                "body": body,
                "to_language": to_language,
                "from_language": from_language,
            }
        )
        return [_FakeResponseItem()]


def test_translate_text_uses_target_language(monkeypatch):
    fake_client = _FakeClient()
    monkeypatch.setattr(translate, "_client", fake_client)

    result = translate.translate_text("你好", target_language="en")

    assert result.detected_language == "zh-Hant"
    assert [item.to for item in result.translations] == ["en", "zh-Hant"]
    assert fake_client.calls[0]["to_language"] == ["en"]
    assert fake_client.calls[0]["from_language"] == "zh-Hant"


def test_translate_to_returns_first_match(monkeypatch):
    fake_client = _FakeClient()
    monkeypatch.setattr(translate, "_client", fake_client)

    text = translate.translate_to("你好", target_language="zh-Hant")

    assert text == "Hello"
    assert fake_client.calls[0]["to_language"] == ["zh-Hant"]
    assert fake_client.calls[0]["from_language"] == "zh-Hant"
