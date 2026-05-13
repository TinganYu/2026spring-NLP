import diary.visualization as viz


SAMPLE_RECORDS = [
    {
        "date": "2026-05-01",
        "sentiment_label": "negative",
        "sentiment_score": 0.2,
        "extra": {
            "phi": {
                "entities": [
                    {"text": "headache", "category": "SymptomOrSign"},
                    {"text": "ibuprofen", "category": "MedicationName"},
                ],
                "relations": [
                    {
                        "relation_type": "TimeOfCondition",
                        "roles": [
                            {"name": "Condition", "entity_text": "headache"},
                            {"name": "Time", "entity_text": "today"},
                        ],
                    }
                ],
            }
        },
    },
    {
        "date": "2026-05-02",
        "sentiment_label": "neutral",
        "sentiment_score": 0.6,
        "extra": {
            "phi": {
                "entities": [
                    {"text": "insomnia", "category": "SymptomOrSign"},
                ],
                "relations": [],
            }
        },
    },
]


def test_build_emotion_line_chart():
    payload = viz.build_emotion_line_chart(SAMPLE_RECORDS)

    assert payload["chart_type"] == "line"
    assert payload["labels"] == ["2026-05-01", "2026-05-02"]
    assert payload["series"][0]["data"] == [-0.2, 0.0]
    assert payload["markers"][0]["emotion_polarity"] == -0.2
    assert payload["markers"][0]["symptoms"] == ["headache"]
    assert payload["markers"][0]["medications"] == ["ibuprofen"]


def test_build_symptom_frequency_chart():
    payload = viz.build_symptom_frequency_chart(SAMPLE_RECORDS)

    assert payload["chart_type"] == "bar"
    assert payload["ranking"][0]["name"] == "headache"
    assert payload["ranking"][0]["count"] == 1


def test_build_emotion_symptom_cooccurrence():
    payload = viz.build_emotion_symptom_cooccurrence(SAMPLE_RECORDS)

    assert payload["chart_type"] == "cooccurrence"
    assert {item["emotion"] for item in payload["emotion_summary"]} == {"negative", "neutral"}
    assert any(item["symptom"] == "headache" and item["count"] == 1 for item in payload["pair_summary"])


def test_build_dashboard_payload():
    payload = viz.build_health_dashboard_payload(SAMPLE_RECORDS)

    assert set(payload.keys()) == {
        "emotion_line_chart",
        "symptom_frequency_chart",
        "medication_frequency_chart",
        "cooccurrence_chart",
    }
