"""跨 entry 的聚合/圖表 Payload 建構器。

將原本散落在 `weekly_summary.py` 與 `visualization.py` 的週聚合與圖表組裝邏輯集中在此，負責：
- 轉換 AnalysisResult 到 DiaryRecord
- 計算情緒基本統計
- 呼叫 visualization 產生 chart payload
"""
from typing import List, Dict, Any
from collections import Counter
from .models import AnalysisResult
from .processor import to_diary_record
from .visualization import (
    build_emotion_line_chart,
    build_symptom_frequency_chart,
    build_medication_frequency_chart,
    build_emotion_symptom_cooccurrence,
    build_symptom_timeline,
    build_symptom_severity_chart,
    build_medication_timeline,
    build_emotion_heatmap_calendar,
    build_cooccurrence_heatmap,
)


def aggregate_weekly_records(records: List[AnalysisResult]) -> Dict[str, Any]:
    """Aggregate 7 days of diary records into weekly analysis."""
    if not records:
        return _empty_weekly_summary()

    # 將 AnalysisResult 轉換為統一的 DiaryRecord 格式
    diary_records = [
        to_diary_record(record, record.entry.meta.get("date") or "")
        for record in records
    ]
    
    # 以日期排序以確保時間軸正確
    diary_records.sort(key=lambda x: x["date"])

    # 產生各種 Visualization payloads
    emotion_line = build_emotion_line_chart(diary_records)
    symptom_freq = build_symptom_frequency_chart(diary_records)
    medication_freq = build_medication_frequency_chart(diary_records)
    cooccurrence = build_emotion_symptom_cooccurrence(diary_records)
    
    symptom_timeline = build_symptom_timeline(diary_records)
    symptom_severity = build_symptom_severity_chart(diary_records)
    medication_timeline = build_medication_timeline(diary_records)
    emotion_heatmap = build_emotion_heatmap_calendar(diary_records)
    cooccurrence_heatmap = build_cooccurrence_heatmap(diary_records)

    # 基礎統計與 PHI relations 留給 Groq 總結使用
    emotion_stats = _calculate_emotion_statistics(diary_records)
    phi_relations = _aggregate_phi_relations(records)

    return {
        "week_start": diary_records[0]["date"] if diary_records else None,
        "week_end": diary_records[-1]["date"] if diary_records else None,
        "record_count": len(diary_records),
        
        # 基礎統計資料
        "emotion_statistics": emotion_stats,
        "phi_relations": phi_relations,
        
        # 圖表 Payloads
        "emotion_line_chart": emotion_line,
        "symptom_frequency_chart": symptom_freq,
        "medication_frequency_chart": medication_freq,
        "cooccurrence_chart": cooccurrence,
        "symptom_timeline": symptom_timeline,
        "symptom_severity_chart": symptom_severity,
        "medication_timeline": medication_timeline,
        "emotion_heatmap_calendar": emotion_heatmap,
        "cooccurrence_heatmap": cooccurrence_heatmap,
    }


def _calculate_emotion_statistics(diary_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not diary_records:
        return {}
    scores = [r["emotion_score"] for r in diary_records]
    labels = [r["emotion_label"] for r in diary_records]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    label_counts = Counter(labels)
    most_common_label = label_counts.most_common(1)[0][0] if label_counts else None
    trend_direction = "stable"
    if len(scores) >= 2:
        trend_value = scores[-1] - scores[0]
        if trend_value > 0.1:
            trend_direction = "improving"
        elif trend_value < -0.1:
            trend_direction = "declining"
            
    return {
        "average_score": round(avg_score, 3),
        "most_common_label": most_common_label,
        "label_distribution": dict(label_counts),
        "trend_direction": trend_direction,
    }


def _aggregate_phi_relations(records: List[AnalysisResult]) -> List[Dict[str, Any]]:
    """這部分仍由原始 AnalysisResult 提取，供 Groq prompt 使用"""
    all_relations = []
    from collections import defaultdict
    for record in records:
        phi_summary = record.extra.get("phi", {})
        relations = phi_summary.get("relations", [])
        for relation in relations:
            all_relations.append({
                "relation_type": relation.get("relation_type"),
                "roles": relation.get("roles", []),
                "date": record.entry.meta.get("date"),
            })
            
    relations_by_type = defaultdict(list)
    for rel in all_relations:
        rel_type = rel.get("relation_type", "Unknown")
        relations_by_type[rel_type].append(rel)
        
    return [
        {"relation_type": rel_type, "occurrences": len(rels), "examples": rels[:2]}
        for rel_type, rels in sorted(relations_by_type.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    ]


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