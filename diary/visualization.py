from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional


# 這個模組不負責 AI 抽取，而是把已經整理好的資料轉成「前端能直接畫圖」的格式。
# 目標是讓 Chart.js / ECharts 可以直接吃 labels、series、markers、rankings 之類的 payload。


def _get(record: Any, key: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        return record.get(key, default)
    return getattr(record, key, default)


def _get_phi(record: Any) -> Dict[str, Any]:
    extra = _get(record, "extra", {}) or {}
    if isinstance(extra, Mapping) and extra.get("phi"):
        return extra.get("phi") or {}

    phi = _get(record, "phi")
    if isinstance(phi, Mapping):
        return phi

    analysis_results = _get(record, "analysis_results", {}) or {}
    if isinstance(analysis_results, Mapping) and analysis_results.get("phi"):
        return analysis_results.get("phi") or {}

    return {}


def _get_date(record: Any) -> str:
    return str(
        _get(record, "date")
        or _get(record, "entry_date")
        or _get(record, "created_at")
        or _get(record, "timestamp")
        or ""
    )


def _normalize_symptom_text(entity: Dict[str, Any]) -> str:
    return entity.get("text") or entity.get("normalized_text") or ""


def _extract_phi_entities(phi: Dict[str, Any], category: str) -> List[Dict[str, Any]]:
    return [entity for entity in phi.get("entities", []) if entity.get("category") == category]


def _extract_phi_relation_items(phi: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(phi.get("relations", []) or [])


def _extract_sentiment_score(record: Any) -> float:
    value = _get(record, "sentiment_score", _get(record, "emotion_score", 0.0))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_sentiment_label(record: Any) -> str:
    return str(_get(record, "sentiment_label", _get(record, "emotion_label", "neutral")))


def _sort_records_by_date(records: Iterable[Any]) -> List[Any]:
    return sorted(records, key=_get_date)


def build_emotion_line_chart(records: Iterable[Any]) -> Dict[str, Any]:
    """把每筆資料整理成情緒折線圖資料。"""
    sorted_records = _sort_records_by_date(records)
    labels = []
    values = []
    markers = []

    for record in sorted_records:
        date_text = _get_date(record)
        labels.append(date_text)
        values.append(_extract_sentiment_score(record))

        phi = _get_phi(record)
        symptom_names = [
            _normalize_symptom_text(entity)
            for entity in _extract_phi_entities(phi, "SymptomOrSign")
            if _normalize_symptom_text(entity)
        ]
        medication_names = [
            _normalize_symptom_text(entity)
            for entity in _extract_phi_entities(phi, "MedicationName")
            if _normalize_symptom_text(entity)
        ]

        markers.append(
            {
                "date": date_text,
                "emotion_label": _extract_sentiment_label(record),
                "emotion_score": _extract_sentiment_score(record),
                "symptoms": symptom_names,
                "medications": medication_names,
                "relations": phi.get("relations", []),
            }
        )

    return {
        "chart_type": "line",
        "labels": labels,
        "series": [
            {
                "name": "emotion_score",
                "label": "Emotion Score",
                "type": "line",
                "data": values,
                "y_axis": "emotion",
            }
        ],
        "markers": markers,
    }


def build_symptom_frequency_chart(records: Iterable[Any], top_n: int = 10) -> Dict[str, Any]:
    """統計症狀/徵象出現頻率，適合做長條圖或詞雲前處理。"""
    counter = Counter()
    for record in records:
        phi = _get_phi(record)
        for entity in _extract_phi_entities(phi, "SymptomOrSign"):
            text = _normalize_symptom_text(entity)
            if text:
                counter[text] += 1

    items = counter.most_common(top_n)
    return {
        "chart_type": "bar",
        "labels": [name for name, _ in items],
        "series": [
            {
                "name": "symptom_frequency",
                "label": "Symptom Frequency",
                "type": "bar",
                "data": [count for _, count in items],
                "y_axis": "count",
            }
        ],
        "ranking": [{"name": name, "count": count} for name, count in items],
    }


def build_medication_frequency_chart(records: Iterable[Any], top_n: int = 10) -> Dict[str, Any]:
    """統計藥物出現頻率，可做排行圖或輔助詞雲。"""
    counter = Counter()
    for record in records:
        phi = _get_phi(record)
        for entity in _extract_phi_entities(phi, "MedicationName"):
            text = _normalize_symptom_text(entity)
            if text:
                counter[text] += 1

    items = counter.most_common(top_n)
    return {
        "chart_type": "bar",
        "labels": [name for name, _ in items],
        "series": [
            {
                "name": "medication_frequency",
                "label": "Medication Frequency",
                "type": "bar",
                "data": [count for _, count in items],
                "y_axis": "count",
            }
        ],
        "ranking": [{"name": name, "count": count} for name, count in items],
    }


def build_emotion_symptom_cooccurrence(records: Iterable[Any]) -> Dict[str, Any]:
    """計算情緒與症狀的同日共現次數，適合做關聯圖。"""
    cooccurrence = Counter()
    emotion_counter = Counter()
    symptom_counter = Counter()

    for record in records:
        emotion_label = _extract_sentiment_label(record)
        emotion_counter[emotion_label] += 1

        phi = _get_phi(record)
        symptoms = [
            _normalize_symptom_text(entity)
            for entity in _extract_phi_entities(phi, "SymptomOrSign")
            if _normalize_symptom_text(entity)
        ]

        for symptom in symptoms:
            symptom_counter[symptom] += 1
            cooccurrence[f"{emotion_label}__{symptom}"] += 1

    emotion_summary = [{"emotion": label, "count": count} for label, count in emotion_counter.most_common()]
    symptom_summary = [{"symptom": symptom, "count": count} for symptom, count in symptom_counter.most_common()]
    pair_summary = [
        {
            "emotion": pair_key.split("__", 1)[0],
            "symptom": pair_key.split("__", 1)[1],
            "count": count,
        }
        for pair_key, count in cooccurrence.most_common()
    ]

    return {
        "chart_type": "cooccurrence",
        "emotion_summary": emotion_summary,
        "symptom_summary": symptom_summary,
        "pair_summary": pair_summary,
    }


def build_health_dashboard_payload(records: Iterable[Any], top_n: int = 10) -> Dict[str, Any]:
    """一次產生前端儀表板常用的所有圖表資料。"""
    records_list = list(records)
    sorted_records = _sort_records_by_date(records_list)
    return {
        "emotion_line_chart": build_emotion_line_chart(sorted_records),
        "symptom_frequency_chart": build_symptom_frequency_chart(sorted_records, top_n=top_n),
        "medication_frequency_chart": build_medication_frequency_chart(sorted_records, top_n=top_n),
        "cooccurrence_chart": build_emotion_symptom_cooccurrence(sorted_records),
    }


if __name__ == "__main__":
    sample_records = [
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
                    "relations": [],
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
    print(build_health_dashboard_payload(sample_records, top_n=5))
