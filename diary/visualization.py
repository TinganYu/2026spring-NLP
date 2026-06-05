"""將已整理好的分析資料轉成前端圖表 payload（labels/series/markers/ranking）。

此模組只負責格式化與統計的視覺化輸出，不直接執行 NLP/PHI 分析。

相較值得保留的：emotion_line_chart（情緒趨勢折線）、symptom_frequency_chart（症狀頻率長條）、medication_frequency_chart（用藥頻率長條）、cooccurrence_chart(情緒-症狀共現分析)。
"""

from collections import Counter, defaultdict
from typing import Dict, List, Any
from datetime import datetime

from .models import DiaryRecord



def build_emotion_line_chart(records: List[DiaryRecord]) -> Dict[str, Any]:
    """情緒極性折線圖資料"""
    sorted_records = sorted(records, key=lambda r: r["date"])
    labels = [] # x 軸標籤，日期
    values = [] # y 軸數值，這裡用情緒極性（positive: 正分, negative: 負分, neutral: 0）表示
    markers = [] # 用於前端顯示的標記點，包含日期、情緒分數、症狀和用藥等資訊，方便前端顯示

    for record in sorted_records:
        date_text = record["date"]
        labels.append(date_text)
        
        score = record["emotion_score"]
        label = record["emotion_label"].lower()
        polarity = -score if label == "negative" else score if label == "positive" else 0.0
        values.append(polarity)

        markers.append({ # 使用者點及某個點時，可以看到這些資訊
            "date": date_text,
            "emotion_label": record["emotion_label"],
            "emotion_score": record["emotion_score"],
            "emotion_polarity": polarity,
            "symptoms": [s["display"] for s in record["symptoms"]],
            "medications": [m["display"] for m in record["medications"]],
        })

    return {
        "chart_type": "line",
        "labels": labels, # x 軸
        "series": [{ # series 是為了支援多條線的格式，這裡我們只有一條線，命名為 emotion_polarity
            "name": "emotion_polarity",
            "label": "Emotion Polarity",
            "type": "line",
            "data": values,
            "y_axis": "emotion",
        }],
        "markers": markers,
    }


def build_symptom_frequency_chart(records: List[DiaryRecord], top_n: int = 10) -> Dict[str, Any]:
    """統計症狀/徵象出現頻率（依賴 normalized key）"""
    counter = Counter()
    
    for record in records:
        for sym in record["symptoms"]:
            key = sym["key"] or sym["display"] # 優先使用key，如果沒有就使用display名稱
            if key:
                counter[key] += 1

    items = counter.most_common(top_n) # (symptom_key, count) 的列表，依頻率排序，取前 top_n
    return {
        "chart_type": "bar",
        "labels": [k for k, _ in items], # x 軸標籤，症狀名稱
        "series": [{
            "name": "symptom_frequency",
            "label": "Symptom Frequency",
            "type": "bar",
            "data": [count for _, count in items],
            "y_axis": "count",
        }],
        "ranking": [{"name": k, "display": k, "count": count} for k, count in items], # 顯示用的排名列表，包含 key、display 名稱和計數，方便前端顯示
    }


def build_medication_frequency_chart(records: List[DiaryRecord], top_n: int = 10, include_only_taken: bool = True) -> Dict[str, Any]:
    """統計藥物出現頻率。

    預設會包含所有藥物（`include_only_taken=False`）。
    若 `include_only_taken=True`，則僅計入 `taken==True` 的藥物（排除未標記為 taken 的）。
    """
    counter = Counter()
    
    for record in records:
        for med in record["medications"]:
            # 若要求只包含 taken 的藥，則排除未標記為 taken 的
            if include_only_taken and not med.get("taken"):
                continue
            key = med["key"] or med["display"]
            if key:
                counter[key] += 1

    items = counter.most_common(top_n)
    return {
        "chart_type": "bar",
        "labels": [k for k, _ in items],
        "series": [{
            "name": "medication_frequency",
            "label": "Medication Frequency",
            "type": "bar",
            "data": [count for _, count in items],
            "y_axis": "count",
        }],
        "ranking": [{"name": k, "display": k, "count": count} for k, count in items],
    }


def build_emotion_symptom_cooccurrence(records: List[DiaryRecord]) -> Dict[str, Any]:
    """計算情緒與症狀的同日共現次數"""
    cooccurrence = Counter()
    emotion_counter = Counter()
    symptom_counter = Counter()

    for record in records:
        emotion_label = record["emotion_label"].lower()
        emotion_counter[emotion_label] += 1

        for sym in record["symptoms"]:
            key = sym["key"] or sym["display"]
            if key:
                symptom_counter[key] += 1
                cooccurrence[f"{emotion_label}__{key}"] += 1 # 情緒跟症狀組合

    return {
        "chart_type": "cooccurrence",
        "emotion_summary": [{"emotion": label, "count": count} for label, count in emotion_counter.most_common()],
        "symptom_summary": [{"symptom": sym, "count": count} for sym, count in symptom_counter.most_common()],
        "pair_summary": [
            {
                "emotion": pair_key.split("__", 1)[0],
                "symptom": pair_key.split("__", 1)[1],
                "count": count,
            }
            for pair_key, count in cooccurrence.most_common()
        ],
    }




def build_health_dashboard_payload(records: List[DiaryRecord], top_n: int = 10) -> Dict[str, Any]:
    """一次產生前端儀表板常用的所有圖表資料。"""
    return {
        "emotion_line_chart": build_emotion_line_chart(records),
        "symptom_frequency_chart": build_symptom_frequency_chart(records, top_n=top_n),
        "medication_frequency_chart": build_medication_frequency_chart(records, top_n=top_n),
        "cooccurrence_chart": build_emotion_symptom_cooccurrence(records),
    }