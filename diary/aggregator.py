"""跨 entry 的聚合/圖表 Payload 建構器。

這裡只做兩件事：
1. 把 `AnalysisResult` 轉成統一的 `DiaryRecord`
2. 交給 `visualization` 產生所有圖表 payload

這樣流程比較直線，閱讀時不用一直在不同格式間跳來跳去。
"""
from typing import List, Dict, Any
from collections import Counter, defaultdict
from .models import AnalysisResult
from .analysis import to_diary_record
from .visualization import build_health_dashboard_payload


def aggregate_weekly_records(records: List[AnalysisResult]) -> Dict[str, Any]:
    """Aggregate 7 days of diary records into weekly analysis."""
    if not records:
        return _empty_weekly_summary()

    # Accept either a list of AnalysisResult objects or already-formed DiaryRecord dicts.
    first = records[0]
    if isinstance(first, dict) and first.get("date"):
        diary_records = list(records)
        phi_sources = None
    else:
        diary_records = [to_diary_record(record, record.entry.meta.get("date") or "") for record in records]
        phi_sources = records

    diary_records.sort(key=lambda x: x["date"])

    dashboard = build_health_dashboard_payload(diary_records)

    scores = [r["emotion_score"] for r in diary_records]
    labels = [r["emotion_label"] for r in diary_records]
    label_counts = Counter(labels)
    emotion_stats = {
        "average_score": round(sum(scores) / len(scores), 3) if scores else 0,
        "most_common_label": label_counts.most_common(1)[0][0] if label_counts else None,
        "label_distribution": dict(label_counts),
        "trend_direction": "stable",
    }
    if len(scores) >= 2:
        trend_value = scores[-1] - scores[0]
        if trend_value > 0.1:
            emotion_stats["trend_direction"] = "improving"
        elif trend_value < -0.1:
            emotion_stats["trend_direction"] = "declining"

    all_relations = []
    if phi_sources is not None:
        for record in phi_sources:
            phi_summary = record.extra.get("phi", {})
            for relation in phi_summary.get("relations", []):
                all_relations.append(
                    {
                        "relation_type": relation.get("relation_type"),
                        "roles": relation.get("roles", []),
                        "date": record.entry.meta.get("date"),
                    }
                )

    grouped_relations = defaultdict(list)
    for relation in all_relations:
        grouped_relations[relation.get("relation_type", "Unknown")].append(relation)

    phi_relations = [
        {"relation_type": rel_type, "occurrences": len(items), "examples": items[:2]}
        for rel_type, items in sorted(grouped_relations.items(), key=lambda item: len(item[1]), reverse=True)[:5]
    ]

    return {
        "week_start": diary_records[0]["date"] if diary_records else None,
        "week_end": diary_records[-1]["date"] if diary_records else None,
        "record_count": len(diary_records),
        "emotion_statistics": emotion_stats,
        "phi_relations": phi_relations,
        **dashboard,
    }


def _empty_weekly_summary() -> Dict[str, Any]:
    return {
        "week_start": None,
        "week_end": None,
        "record_count": 0,
        "emotion_statistics": {},
        "phi_relations": [],
        "emotion_line_chart": {},
        "symptom_frequency_chart": {},
        "medication_frequency_chart": {},
        "cooccurrence_chart": {},
        "symptom_timeline": {},
        "symptom_severity_chart": {},
        "medication_timeline": {},
        "emotion_heatmap_calendar": {},
        "cooccurrence_heatmap": {},
    }