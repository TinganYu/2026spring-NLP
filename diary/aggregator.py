"""跨 entry 的聚合/圖表 Payload 建構器。

這裡只做兩件事：
1. 接收已整理好的 `DiaryRecord`
2. 交給 `visualization` 產生所有圖表 payload

這樣流程比較直線，閱讀時不用一直在不同格式間跳來跳去。
"""
from typing import List, Dict, Any
from collections import Counter, defaultdict
from .models import DiaryRecord
from .visualization import build_health_dashboard_payload


def aggregate_weekly_records(records: List[DiaryRecord]) -> Dict[str, Any]:
    """Aggregate n days of diary records into weekly analysis.
    (會從app.py決定提供幾天的內容，根據那些資料畫表格，不限於7天)
    接收 DiaryRecord 列表並生成圖表。
    """
    if not records:
        return {
            "week_start": None,
            "week_end": None,
            "record_count": 0,
            "emotion_statistics": {},
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

    diary_records = sorted(records, key=lambda x: x["date"])

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
    if len(scores) >= 2:  # 如果有兩筆以上的資料，才計算趨勢
        polarities = [
            (-r["emotion_score"] if r["emotion_label"].lower() == "negative"
             else r["emotion_score"] if r["emotion_label"].lower() == "positive"
             else 0.0)  # 這邊預設 neutral 是 0，negative 是負分，positive 是正分
            for r in diary_records
        ]
        # 計算簡單的線性趨勢（slope），判斷情緒是改善、惡化還是穩定
        n = len(polarities)
        mean_x = (n - 1) / 2
        mean_y = sum(polarities) / n
        numerator = sum((idx - mean_x) * (value - mean_y) for idx, value in enumerate(polarities))
        denominator = sum((idx - mean_x) ** 2 for idx in range(n))
        slope = (numerator / denominator) if denominator else 0.0
        trend_value = slope * (n - 1)
        if trend_value > 0.1:
            emotion_stats["trend_direction"] = "improving"
        elif trend_value < -0.1:
            emotion_stats["trend_direction"] = "declining"

    return {
        "week_start": diary_records[0]["date"] if diary_records else None,
        "week_end": diary_records[-1]["date"] if diary_records else None,
        "record_count": len(diary_records),
        "emotion_statistics": emotion_stats,  # 情緒趨勢統計
        **dashboard,  # 包含所有圖表 payload (** 把dashboard dict裡的key/value攤平加入/合併最終回傳的dict)
    }

