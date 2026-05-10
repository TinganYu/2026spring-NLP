import shared.phi as phi


class _FakeTranslationItem:
    def __init__(self, text, to):
        self.text = text
        self.to = to


class _FakeTranslationResult:
    def __init__(self, source_text, detected_language, translations):
        self.source_text = source_text
        self.detected_language = detected_language
        self.translations = translations


class _FakeEntity:
    def __init__(self, text, category, normalized_text=None, subcategory=None, offset=0, confidence_score=0.9):
        self.text = text
        self.normalized_text = normalized_text
        self.category = category
        self.subcategory = subcategory
        self.offset = offset
        self.confidence_score = confidence_score
        self.data_sources = []
        self.assertion = None


class _FakeRoleEntity:
    def __init__(self, text):
        self.text = text


class _FakeRole:
    def __init__(self, name, entity_text):
        self.name = name
        self.entity = _FakeRoleEntity(entity_text)


class _FakeRelation:
    def __init__(self, relation_type):
        self.relation_type = relation_type
        self.roles = [_FakeRole("Arg1", "ibuprofen")]


class _FakeDoc:
    is_error = False

    def __init__(self):
        self.entities = [_FakeEntity("ibuprofen", "MedicationName")]
        self.entity_relations = [_FakeRelation("DOSAGE_OF_MEDICATION")]


class _FakePoller:
    def result(self):
        return [_FakeDoc()]


class _FakeClient:
    def __init__(self):
        self.calls = []

    def begin_analyze_healthcare_entities(self, documents, language=None):
        self.calls.append({"documents": documents, "language": language})
        return _FakePoller()


def test_analyze_healthcare_entities_translates_then_analyzes(monkeypatch):
    fake_translation = _FakeTranslationResult(
        source_text="今天頭痛，請吃 ibuprofen 100mg twice daily",
        detected_language="zh-Hant",
        translations=[_FakeTranslationItem("Today headache, take ibuprofen 100mg twice daily", "en")],
    )
    fake_client = _FakeClient()

    monkeypatch.setattr(phi, "translate_text", lambda *args, **kwargs: fake_translation)
    monkeypatch.setattr(phi, "_client", fake_client)

    result = phi.analyze_healthcare_entities("今天頭痛，請吃 ibuprofen 100mg twice daily", target_language="en")

    assert result.original_text.startswith("今天")
    assert result.translated_text == "Today headache, take ibuprofen 100mg twice daily"
    assert result.detected_language == "zh-Hant"
    assert result.entities[0].text == "ibuprofen"
    assert result.relations[0].relation_type == "DOSAGE_OF_MEDICATION"
    assert fake_client.calls[0]["documents"] == ["Today headache, take ibuprofen 100mg twice daily"]
    assert fake_client.calls[0]["language"] == "en"


def test_analyze_healthcare_entities_accepts_pretranslated_text(monkeypatch):
    fake_client = _FakeClient()
    monkeypatch.setattr(phi, "_client", fake_client)

    result = phi.analyze_healthcare_entities(
        "今天頭痛，請吃 ibuprofen 100mg twice daily",
        target_language="en",
        translated_text="Today headache, take ibuprofen 100mg twice daily",
        include_translation=False,
    )

    assert result.translated_text == "Today headache, take ibuprofen 100mg twice daily"
    assert fake_client.calls[0]["documents"] == ["Today headache, take ibuprofen 100mg twice daily"]
