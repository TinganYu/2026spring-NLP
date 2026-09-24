"""所有多餘的程式我捨不得刪就再這裡放著，免得以後還會用到"""

# ==============analysis.py裡面被刪掉的程式======================

#舊的程式
# 1. 整理 Symptoms
    symptom_records = []
    for ent in entities:
        if ent.get("category") == "SymptomOrSign":
            key = ent.get("normalized_text") or ent.get("text") or ""
            display = ent.get("text") or ""

            status = _infer_entity_status(ent)
            times: List[str] = []       # 特別抓出時間
            body: List[str] = []        # 特別抓出身體部位
            frequencies: List[str] = [] # 特別抓出頻率
            # notes: Dict[str, List[str]] = {} # 存放所有與該症狀相關的其他 Relation 屬性
            
            max_severity = 1
            for rel in relations: # 在所有relation中找出有連到這個症狀的
                roles = rel.get("roles", [])
                
                cond_text = _get_role_text(roles, "Condition", "Symptom", "Entity")
                if cond_text != display: # 如果跟我目前要找的症狀不一樣就跳過
                    continue

                rtype = rel.get("relation_type")
                if rtype == "QualifierOfCondition":
                        qualifier = _get_role_text(roles, "Qualifier")
                        if qualifier and qualifier.lower() in SEVERITY_MAP:
                            max_severity = max(max_severity, SEVERITY_MAP[qualifier.lower()]) # 找對應的等級，沒有就用預設1
                # 獨立抓取時間
                elif rtype == "TimeOfCondition": 
                    val = _get_role_text(roles, "Time", "Date") # 找出任何 role(關係類型) 是 time 或 date 的 entity
                    if val:
                        times.append(val)
                # 獨立抓取身體部位
                elif rtype == "BodySiteOfCondition":
                    val = _get_role_text(roles, "BodySite")
                    if val:
                        body.append(val)

                # 獨立抓取頻率
                elif rtype == "FrequencyOfCondition":
                    val = _get_role_text(roles, "Frequency")
                    if val:
                        frequencies.append(val)

            symptom_records.append(SymptomRecord(
                key=key,
                display=display,
                status=status,
                severity=max_severity,
                times=times,             
                frequencies=frequencies, 
                # notes=notes
            ))

    # 2. 整理 Medications（改為累積劑量/頻率/註記為 list）
    medication_records = []
    for ent in entities:
        if ent.get("category") == "MedicationName":
            key = ent.get("normalized_text") or ent.get("text") or ""
            display = ent.get("text") or ""

            dosages: List[str] = []
            frequencies: List[str] = []
            notes: Dict[str, List[str]] = {} # 改為字典結構存放其他屬性

            for rel in relations:
                roles = rel.get("roles", [])
                med_text = _get_role_text(roles, "Medication", "Drug")
                if med_text != display: # relation裡存的是text不是normalized_text，所以用display來比對
                    continue

                rtype = rel.get("relation_type")
                if rtype == "DosageOfMedication":
                    val = _get_role_text(roles, "Dosage")
                    if val:
                        dosages.append(val)
                elif rtype == "FrequencyOfMedication":
                    val = _get_role_text(roles, "Frequency")
                    if val:
                        frequencies.append(val)

            # medication 推論為 True 當且僅當 entity 有 assertion 且 status 為 affirmed
            med_status = _infer_entity_status(ent)
            taken_flag = (med_status == "affirmed") and bool(ent.get("assertion"))
            medication_records.append(MedicationRecord(
                key=key,
                display=display,
                dosages=dosages,
                frequencies=frequencies,
                # notes=notes,
                taken=taken_flag
            ))


# # 其他屬性 (部位、程度等) 丟進 notes
                # elif rtype:                  
                    
                #     if rtype not in notes:
                #         notes[rtype] = []
                    
                #     for role in roles:
                #         role_name = role.get("name")
                #         role_text = role.get("entity_text")
                        
                #         # 排除掉指向症狀本身的 role
                #         if role_name not in ("Condition", "Symptom", "Entity") and role_text:
                #             notes[rtype].append(role_text)




                # elif rtype:
                #     # 其他和藥物有關的 relation 當作註記保留，結構為 Dict[str, List[str]]，範例 {"RouteOfAdministration": ["口服"], "FormOfMedication": ["錠劑"]}
                #     if rtype not in notes:
                #         notes[rtype] = []
                    
                #     # 找出該 relation 中，除了「藥物本身」以外的實體文字並塞進 List
                #     for role in roles:
                #         role_name = role.get("name")
                #         role_text = role.get("entity_text")
                        
                #         # 排除掉指向藥物本身的 role (如 Medication, Drug)，只存屬性值 (如 Route, Form 等)
                #         if role_name not in ("Medication", "Drug") and role_text:
                #             notes[rtype].append(role_text)




## =====下方是針對PHI分析結果的進階整理功能，提供給月底回顧和看診準備使用=======
# def build_correlation_discovery(phi: Dict[str, Any], emotion_label: str = None) -> Dict[str, Any]:
#     """把 PHI 結果整理成可做月底回顧的關聯摘要。

#     這裡會把 Emotion、SymptomOrSign、MedicationName、assertion、relation
#     整理成適合做趨勢觀察的資料。
#     """
#     entities = phi.get("entities", [])
#     relations = phi.get("relations", [])

#     # 統計每種 entity category 出現次數
#     categories = Counter(entity.get("category") for entity in entities if entity.get("category"))

#     medications = [entity for entity in entities if entity.get("category") == "MedicationName"]
#     assertions = [
#         {
#             "text": entity.get("text") or entity.get("normalized_text") or "",
#             "category": entity.get("category"), # category內容可能是 SymptomOrSign、MedicationName 等等
#             "conditionality": entity.get("assertion", {}).get("conditionality"),
#             "certainty": entity.get("assertion", {}).get("certainty"),
#             "association": entity.get("assertion", {}).get("association"),
#         }
#         for entity in entities
#         if entity.get("assertion")
#     ]

#     relation_facts = []
#     for relation in relations:
#         relation_type = relation.get("relation_type") or "Unknown"
#         roles = {role.get("name") or "Unknown": role.get("entity_text") or "" for role in relation.get("roles", [])}
#         relation_facts.append(
#             {
#                 "relation_type": relation_type,
#                 "roles": roles,
#                 "text": _format_relation_text(relation_type, roles),
#             }
#         )

#     return {
#         "emotion_label": emotion_label,
#         "category_counts": dict(categories),
#         "medications": medications,
#         "relation_facts": relation_facts,
#         "assertions": assertions,
#     }


# def build_doctor_visit_prep(phi: Dict[str, Any]) -> Dict[str, Any]:
#     """把 PHI 結果整理成看診前可直接輸出的懶人包。

#     目標是快速列出：症狀、持續時間、嚴重程度、用藥與相關時間線。
#     """
#     entities = phi.get("entities", [])
#     relations = phi.get("relations", [])

#     # 這些欄位是看診時最常需要說明的內容
#     symptom_or_sign = [entity for entity in entities if entity.get("category") == "SymptomOrSign"]
#     durations = [entity for entity in entities if entity.get("category") == "Duration"]
#     qualifiers = [entity for entity in entities if entity.get("category") == "ConditionQualifier"]
#     medications = [entity for entity in entities if entity.get("category") == "MedicationName"]

#     # 這裡只保留和時間、持續時間、頻率有關的 relation
#     timeline_items = []
#     for relation in relations:
#         relation_type = relation.get("relation_type") or "Unknown"
#         roles = {role.get("name") or "Unknown": role.get("entity_text") or "" for role in relation.get("roles", [])}
#         if relation_type in {"TimeOfCondition", "DurationOfCondition", "FrequencyOfMedication"}:
#             timeline_items.append(
#                 {
#                     "relation_type": relation_type,
#                     "roles": roles,
#                     "text": _format_relation_text(relation_type, roles),
#                 }
#             )

#     assertion_flags = [
#         {
#             "text": entity.get("text") or entity.get("normalized_text") or "",
#             "category": entity.get("category"),
#             "conditionality": entity.get("assertion", {}).get("conditionality"),
#             "certainty": entity.get("assertion", {}).get("certainty"),
#             "association": entity.get("assertion", {}).get("association"),
#         }
#         for entity in entities
#         if entity.get("assertion")
#     ]

#     return {
#         # `symptom_or_sign` 在看診懶人包需要完整實體，保留此處輸出（on-demand）
#         "symptom_or_sign": symptom_or_sign,
#         "durations": durations,
#         "qualifiers": qualifiers,
#         "medications": medications,
#         "timeline_items": timeline_items,
#         "assertions": assertion_flags,
#         "suggested_summary": _build_visit_summary(symptom_or_sign, durations, qualifiers, medications, timeline_items),
#     }

# 這個可能沒用可以刪掉，先保留在這裡當作參考
# def _format_relation_text(relation_type: str, roles: Dict[str, str]) -> str:
#     # 把 relation 轉成中文可讀句子，方便前端顯示或報告使用
#     if relation_type == "TimeOfCondition":
#         condition = roles.get("Condition") or roles.get("Symptom") or roles.get("Entity") or "某個症狀"
#         time_value = roles.get("Time") or roles.get("Date") or "某個時間"
#         return f"{condition} 發生在 {time_value}"

#     if relation_type == "DurationOfCondition":
#         condition = roles.get("Condition") or roles.get("Symptom") or "某個症狀"
#         duration = roles.get("Duration") or "某段時間"
#         return f"{condition} 持續 {duration}"

#     if relation_type == "DosageOfMedication":
#         medication = roles.get("Medication") or roles.get("Drug") or "某個藥物"
#         dosage = roles.get("Dosage") or "某個劑量"
#         return f"{medication} 的劑量是 {dosage}"

#     if relation_type == "FrequencyOfMedication":
#         medication = roles.get("Medication") or roles.get("Drug") or "某個藥物"
#         frequency = roles.get("Frequency") or "某個頻率"
#         return f"{medication} 的服用頻率是 {frequency}"

#     return f"{relation_type}: {', '.join(f'{k}={v}' for k, v in roles.items())}"

# def _build_visit_summary(
#     symptom_or_sign: List[Dict[str, Any]],
#     durations: List[Dict[str, Any]],
#     qualifiers: List[Dict[str, Any]],
#     medications: List[Dict[str, Any]],
#     timeline_items: List[Dict[str, Any]],
# ) -> List[str]:
#     # 這裡產生最終的看診前摘要，一行一個重點
#     lines = []

#     if symptom_or_sign:
#         symptom_texts = [entity.get("text") for entity in symptom_or_sign if entity.get("text")]
#         lines.append(f"症狀/徵象：{', '.join(symptom_texts)}")

#     if durations:
#         duration_texts = [entity.get("text") for entity in durations if entity.get("text")]
#         lines.append(f"持續時間：{', '.join(duration_texts)}")

#     if qualifiers:
#         qualifier_texts = [entity.get("text") for entity in qualifiers if entity.get("text")]
#         lines.append(f"程度/狀態：{', '.join(qualifier_texts)}")

#     if medications:
#         medication_texts = [entity.get("text") for entity in medications if entity.get("text")]
#         lines.append(f"藥物：{', '.join(medication_texts)}")

#     for item in timeline_items:
#         if item.get("text"):
#             lines.append(item["text"])

#     return lines


# =================translate.py裡面被刪掉的程式======================




# ============= Convenience function for common use case =============
# 只回傳第一個翻譯結果的文本，適合大多數只需要單一翻譯的情況。
def translate_to(text: str, target_language: str, source_language: Optional[str] = None) -> str:
    """Translate text and return the first translated string for the requested target language."""
    result = translate_text(text, target_language=target_language, source_language=source_language)
    # result is now a dict
    if not result.get("translations"):
        return text
    return result["translations"][0]["text"]




# =================app.py裡面被刪掉的程式======================
# @app.route("/api/entity-mapping/<entity_id>", methods=["GET"]) # 之後如果有做需要entity標籤的東西才會需要，請無視
# def get_entity_mapping(entity_id):
#     # 從數據庫取得完整的entity數據(尤其是data sources)
#     # 之後建好再加入程式
#     pass


# =================groq.py裡面被刪掉的程式======================
def build_weekly_groq_payload(weekly_payload: Dict[str, Any]) -> Dict[str, Any]:
    """將週報聚合結果整理成 Groq 的輸入 payload，避免把完整 dashboard 直接塞進 prompt。"""
    return {
        "week_start": weekly_payload.get("week_start"),
        "week_end": weekly_payload.get("week_end"),
        "record_count": weekly_payload.get("record_count", 0),
        "emotion_statistics": weekly_payload.get("emotion_statistics", {}),
        "emotion_line_chart": weekly_payload.get("emotion_line_chart", {}),
        "symptom_frequency_chart": weekly_payload.get("symptom_frequency_chart", {}),
        "medication_frequency_chart": weekly_payload.get("medication_frequency_chart", {}),
        "cooccurrence_chart": weekly_payload.get("cooccurrence_chart", {}),
        "symptom_timeline": weekly_payload.get("symptom_timeline", {}),
        "medication_timeline": weekly_payload.get("medication_timeline", {}),
        "emotion_heatmap_calendar": weekly_payload.get("emotion_heatmap_calendar", {}),
        "cooccurrence_heatmap": weekly_payload.get("cooccurrence_heatmap", {}),
    }


# =================visualization.py裡面被刪掉的程式======================
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