"""將已整理好的分析資料轉成前端圖表 payload（labels/series/markers/ranking）。

此模組只負責格式化與統計的視覺化輸出，不直接執行 NLP/PHI 分析。

相較值得保留的：emotion_line_chart（情緒趨勢折線）、symptom_frequency_chart（症狀頻率長條）、medication_frequency_chart（用藥頻率長條）、symptom_timeline（症狀出現/消失甘特圖）
比較不直覺: cooccurrence_chart 和 cooccurrence_heatmap
"""

from collections import Counter, defaultdict
from typing import Dict, List, Any
from datetime import datetime

from .models import DiaryRecord


def _sort_records_by_date(records: List[DiaryRecord]) -> List[DiaryRecord]:
    return sorted(records, key=lambda r: r["date"])


def build_emotion_line_chart(records: List[DiaryRecord]) -> Dict[str, Any]:
    """情緒極性折線圖資料"""
    sorted_records = _sort_records_by_date(records)
    labels = []
    values = []
    markers = []

    for record in sorted_records:
        date_text = record["date"]
        labels.append(date_text)
        
        score = record["emotion_score"]
        label = record["emotion_label"].lower()
        polarity = -score if label == "negative" else score if label == "positive" else 0.0
        values.append(polarity)

        markers.append({
            "date": date_text,
            "emotion_label": record["emotion_label"],
            "emotion_score": record["emotion_score"],
            "emotion_polarity": polarity,
            "symptoms": [s["display"] for s in record["symptoms"]],
            "medications": [m["display"] for m in record["medications"]],
        })

    return {
        "chart_type": "line",
        "labels": labels,
        "series": [{
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
    name_map = {}
    
    for record in records:
        for sym in record["symptoms"]:
            key = sym["key"] or sym["display"]
            if key:
                counter[key] += 1
                name_map[key] = sym["display"]

    items = counter.most_common(top_n)
    return {
        "chart_type": "bar",
        "labels": [name_map.get(k, k) for k, _ in items],
        "series": [{
            "name": "symptom_frequency",
            "label": "Symptom Frequency",
            "type": "bar",
            "data": [count for _, count in items],
            "y_axis": "count",
        }],
        "ranking": [{"name": k, "display": name_map.get(k, k), "count": count} for k, count in items],
    }


def build_medication_frequency_chart(records: List[DiaryRecord], top_n: int = 10) -> Dict[str, Any]:
    """統計藥物出現頻率"""
    counter = Counter()
    name_map = {}
    
    for record in records:
        for med in record["medications"]:
            key = med["key"] or med["display"]
            if key:
                counter[key] += 1
                name_map[key] = med["display"]

    items = counter.most_common(top_n)
    return {
        "chart_type": "bar",
        "labels": [name_map.get(k, k) for k, _ in items],
        "series": [{
            "name": "medication_frequency",
            "label": "Medication Frequency",
            "type": "bar",
            "data": [count for _, count in items],
            "y_axis": "count",
        }],
        "ranking": [{"name": k, "display": name_map.get(k, k), "count": count} for k, count in items],
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
                cooccurrence[f"{emotion_label}__{key}"] += 1

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


def build_symptom_timeline(records: List[DiaryRecord]) -> Dict[str, Any]:
    """症狀出現/消失事件流，甘特圖風格"""
    sorted_records = _sort_records_by_date(records)
    tracker = {}

    for record in sorted_records:
        date_str = record["date"]
        curr_date = datetime.strptime(date_str, "%Y-%m-%d")

        for sym in record["symptoms"]:
            k = sym["key"] or sym["display"]
            status = sym["status"]

            if k not in tracker:
                tracker[k] = {
                    "display": sym["display"],
                    "current_span": {"start": date_str, "end": date_str, "status": status},
                    "spans": []
                }
            else:
                last_end_str = tracker[k]["current_span"]["end"]
                last_end_date = datetime.strptime(last_end_str, "%Y-%m-%d")
                last_status = tracker[k]["current_span"]["status"]

                if (curr_date - last_end_date).days == 1 and last_status == status:
                    tracker[k]["current_span"]["end"] = date_str
                else:
                    tracker[k]["spans"].append(tracker[k]["current_span"])
                    tracker[k]["current_span"] = {"start": date_str, "end": date_str, "status": status}

    symptoms_out = []
    for k, data in tracker.items():
        if data["current_span"]:
            data["spans"].append(data["current_span"])
        symptoms_out.append({
            "name": k,
            "display": data["display"],
            "spans": data["spans"]
        })

    return {"chart_type": "timeline", "symptoms": symptoms_out}


# def build_symptom_severity_chart(records: List[DiaryRecord]) -> Dict[str, Any]:
#     """症狀嚴重程度趨勢，多線折線圖（過濾掉全為 1 的症狀）"""
#     sorted_records = _sort_records_by_date(records)
#     labels = [r["date"] for r in sorted_records]
#
#     # 疼痛/嚴重程度指數目前未入庫，先停用長期趨勢圖
#     severity_map = defaultdict(lambda: [None] * len(sorted_records))
#     display_map = {}
#     valid_keys = set()
#
#     for i, record in enumerate(sorted_records):
#         for sym in record["symptoms"]:
#             k = sym["key"] or sym["display"]
#             display_map[k] = sym["display"]
#             severity_map[k][i] = sym["severity"]
#             if sym["severity"] > 0:
#                 valid_keys.add(k)
#
#     series = []
#     for k in valid_keys:
#         series.append({
#             "name": k,
#             "display": display_map[k],
#             "data": severity_map[k]
#         })
#
#     return {
#         "chart_type": "multi_line",
#         "labels": labels,
#         "series": series
#     }


def build_medication_timeline(records: List[DiaryRecord]) -> Dict[str, Any]:
    """用藥時間軸，區分明確記錄與推斷延續"""
    sorted_records = _sort_records_by_date(records)
    tracker = {}

    for record in sorted_records:
        date_str = record["date"]
        curr_date = datetime.strptime(date_str, "%Y-%m-%d")

        for med in record["medications"]:
            k = med["key"] or med["display"]
            inferred = med["inferred"]

            if k not in tracker:
                tracker[k] = {
                    "display": med["display"],
                    "current_span": {"start": date_str, "end": date_str, "inferred": inferred},
                    "spans": []
                }
            else:
                last_end_str = tracker[k]["current_span"]["end"]
                last_end_date = datetime.strptime(last_end_str, "%Y-%m-%d")
                last_inferred = tracker[k]["current_span"]["inferred"]

                if (curr_date - last_end_date).days == 1 and last_inferred == inferred:
                    tracker[k]["current_span"]["end"] = date_str
                else:
                    tracker[k]["spans"].append(tracker[k]["current_span"])
                    tracker[k]["current_span"] = {"start": date_str, "end": date_str, "inferred": inferred}

    medications_out = []
    for k, data in tracker.items():
        if data["current_span"]:
            data["spans"].append(data["current_span"])
        medications_out.append({
            "name": k,
            "display": data["display"],
            "spans": data["spans"]
        })

    return {"chart_type": "timeline", "medications": medications_out}


def build_emotion_heatmap_calendar(records: List[DiaryRecord]) -> Dict[str, Any]:
    """週曆熱力圖"""
    data = []
    for record in records:
        score = record["emotion_score"]
        label = record["emotion_label"].lower()
        polarity = -score if label == "negative" else score if label == "positive" else 0.0
        data.append({
            "date": record["date"],
            "value": polarity,
            "label": label
        })

    return {
        "chart_type": "calendar_heatmap",
        "data": sorted(data, key=lambda x: x["date"])
    }


def build_cooccurrence_heatmap(records: List[DiaryRecord]) -> Dict[str, Any]:
    """情緒×症狀熱力圖矩陣"""
    y_labels = ["positive", "neutral", "negative"]
    symptom_counter = Counter()
    
    # 計算各症狀頻率，用於 x 軸排序
    for record in records:
        for sym in record["symptoms"]:
            symptom_counter[sym["key"] or sym["display"]] += 1
            
    sorted_symptoms = [k for k, _ in symptom_counter.most_common()]
    x_labels = []
    x_keys = []
    
    # 建立反查表取得顯示名稱
    display_map = {}
    for record in records:
        for sym in record["symptoms"]:
            k = sym["key"] or sym["display"]
            if k not in display_map:
                display_map[k] = sym["display"]

    for k in sorted_symptoms:
        x_keys.append(k)
        x_labels.append(display_map[k])

    # 初始化矩陣 [y][x]
    matrix = [[0] * len(sorted_symptoms) for _ in range(3)]
    emotion_idx = {label: i for i, label in enumerate(y_labels)}

    for record in records:
        e_label = record["emotion_label"].lower()
        if e_label in emotion_idx:
            y = emotion_idx[e_label]
            for sym in record["symptoms"]:
                k = sym["key"] or sym["display"]
                if k in sorted_symptoms:
                    x = sorted_symptoms.index(k)
                    matrix[y][x] += 1

    return {
        "chart_type": "heatmap",
        "x_labels": x_labels,
        "y_labels": y_labels,
        "matrix": matrix,
        "x_keys": x_keys,
    }


def build_health_dashboard_payload(records: List[DiaryRecord], top_n: int = 10) -> Dict[str, Any]:
    """一次產生前端儀表板常用的所有圖表資料。"""
    return {
        "emotion_line_chart": build_emotion_line_chart(records),
        "symptom_frequency_chart": build_symptom_frequency_chart(records, top_n=top_n),
        "medication_frequency_chart": build_medication_frequency_chart(records, top_n=top_n),
        "cooccurrence_chart": build_emotion_symptom_cooccurrence(records),
        "symptom_timeline": build_symptom_timeline(records),
        # "symptom_severity_chart": build_symptom_severity_chart(records),
        "medication_timeline": build_medication_timeline(records),
        "emotion_heatmap_calendar": build_emotion_heatmap_calendar(records),
        "cooccurrence_heatmap": build_cooccurrence_heatmap(records),
    }