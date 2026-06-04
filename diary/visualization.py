"""將已整理好的分析資料轉成前端圖表 payload（labels/series/markers/ranking）。

此模組只負責格式化與統計的視覺化輸出，不直接執行 NLP/PHI 分析。

相較值得保留的：emotion_line_chart（情緒趨勢折線）、symptom_frequency_chart（症狀頻率長條）、medication_frequency_chart（用藥頻率長條）、symptom_timeline（症狀出現/消失甘特圖）
比較不直覺: cooccurrence_chart 和 cooccurrence_heatmap
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


def build_symptom_timeline(records: List[DiaryRecord]) -> Dict[str, Any]:
    """症狀出現/消失事件流，甘特圖風格"""
    sorted_records = sorted(records, key=lambda r: r["date"])
    tracker = {}

    for record in sorted_records:
        date_str = record["date"]
        curr_date = datetime.strptime(date_str, "%Y-%m-%d") # 將日期字串轉成 datetime 物件，方便計算日期差異

        for sym in record["symptoms"]:
            k = sym["key"] or sym["display"]
            status = sym["status"]
            if status != "affirmed" and status != "negated": # 目前只追蹤 affirmed 和 negated 的狀態變化，其他狀態（hypothetical、historical、other_person、uncertain）暫不處理
                continue

            if k not in tracker: # 如果這個症狀還沒有在 tracker 中，直接新增一個新的追蹤項目
                tracker[k] = {
                    "display": k,
                    "current_span": {"start": date_str, "end": date_str, "status": status},
                    "spans": [] # 用來存放已完成的 span
                }
            else:
                last_end_str = tracker[k]["current_span"]["end"] # 取得目前追蹤的最後日期
                last_end_date = datetime.strptime(last_end_str, "%Y-%m-%d") 
                last_status = tracker[k]["current_span"]["status"]

                if (curr_date - last_end_date).days == 1 and last_status == status: # 如果日期是連續的且狀態相同，則延續目前的 span
                    tracker[k]["current_span"]["end"] = date_str # 更新結束日期
                else:
                    tracker[k]["spans"].append(tracker[k]["current_span"]) # 否則將目前的 span 存到 spans 列表中，並開始一個新的 span
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


def build_symptom_severity_chart(records: List[DiaryRecord]) -> Dict[str, Any]:
    """症狀嚴重程度趨勢，多線折線圖（過濾掉全為 1 的症狀）"""
    sorted_records = sorted(records, key=lambda r: r["date"])
    labels = [r["date"] for r in sorted_records]

    severity_map = defaultdict(lambda: [None] * len(sorted_records))
    valid_keys = set()

    for i, record in enumerate(sorted_records):
        for sym in record["symptoms"]:
            k = sym["key"] or sym["display"]
            severity_map[k][i] = sym["severity"]
            if sym["severity"] > 0:
                valid_keys.add(k)

    series = [] # 每個症狀一條線，包含 name（key）、display（顯示名稱）和 data（每一天的 severity 值）
    for k in valid_keys:
        series.append({
            "name": k,
            "display": k,
            "data": severity_map[k]
        })

    return {
        "chart_type": "multi_line",
        "labels": labels,
        "series": series
    }


def build_medication_timeline(records: List[DiaryRecord]) -> Dict[str, Any]:
    """用藥時間軸，區分明確記錄與推斷延續"""
    sorted_records = sorted(records, key=lambda r: r["date"])
    tracker = {}

    for record in sorted_records:
        date_str = record["date"]
        curr_date = datetime.strptime(date_str, "%Y-%m-%d")

        for med in record["medications"]:
            k = med["key"] or med["display"]
            taken = med["taken"]

            if k not in tracker:
                tracker[k] = {
                    "display": k,
                    "current_span": {"start": date_str, "end": date_str, "taken": taken},
                    "spans": []
                }
            else:
                last_end_str = tracker[k]["current_span"]["end"]
                last_end_date = datetime.strptime(last_end_str, "%Y-%m-%d")
                last_taken = tracker[k]["current_span"]["taken"]

                if (curr_date - last_end_date).days == 1 and last_taken == taken:
                    tracker[k]["current_span"]["end"] = date_str
                else:
                    tracker[k]["spans"].append(tracker[k]["current_span"])
                    tracker[k]["current_span"] = {"start": date_str, "end": date_str, "taken": taken}

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
        "symptom_severity_chart": build_symptom_severity_chart(records),
        "medication_timeline": build_medication_timeline(records),
        "emotion_heatmap_calendar": build_emotion_heatmap_calendar(records),
        "cooccurrence_heatmap": build_cooccurrence_heatmap(records),
    }