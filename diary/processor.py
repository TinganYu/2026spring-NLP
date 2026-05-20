"""Per-entry processing: 以單筆日記文本產生標準化的 `AnalysisResult`。

職責：偵測情緒、呼叫 PHI 分析、回傳可存入 DB 的結構化結果。
不要在這裡做昂貴的跨筆聚合或 on-demand 的深度分析。
"""


from .models import DiaryEntry, AnalysisResult
from .emotion import detect_emotion
from shared.phi import analyze_healthcare_entities

PHI_INTERESTING_CATEGORIES = {
    "SymptomOrSign",
    "MedicationName",
    "Dosage",
    "Frequency",
    "RouteOfAdministration",
    "BodyStructure",
    "Diagnosis",
    "ProcedureName",
    "TestName",
    "TreatmentName",
    "Duration",
    "ConditionQualifier",
}
# SCORE_PATTERNS = [
#                 r'疼痛[程度級別指數]*\s*(\d+)\s*[分級]?',   # 疼痛程度4分、疼痛4級
#                 r'痛[到了]?\s*(\d+)\s*[分級]',              # 痛到8分
#                 r'[不舒服難受]*程度\s*(\d+)\s*[分級]?',      # 不舒服程度3分
#                 r'(\d+)\s*/\s*10',                          # 4/10
#             ]
# _summarize_phi 已註解：若將來需要可恢復或搬到共用工具
# def _summarize_phi(health_result):
#     entities = [asdict(entity) for entity in health_result.entities]  # 把dataclass全部轉成dict
#     relations = [asdict(relation) for relation in health_result.relations]
#
#     # 加入一些其他的索引或分類，方便後續分析使用
#     entities_by_category = {}
#     for entity in entities:
#         category = entity["category"] or "Unknown"
#         entities_by_category.setdefault(category, []).append(entity)
#
#     important_entities = [
#         entity
#         for entity in entities
#         if entity["category"] in PHI_INTERESTING_CATEGORIES
#     ]
#
#     # 只回傳最常使用且必要的欄位，其他衍生索引可由上層按需產生
#     return {
#         "entities": entities,
#         "relations": relations,
#     }

# 最主要的 function：把單筆日記文本轉成 AnalysisResult
def process_entry(text: str, meta: dict = None) -> AnalysisResult:
    """Orchestrator: receives a diary text and returns structured analysis."""
    processed_text = text

    entry: DiaryEntry = {"text": processed_text, "meta": meta or {}}
    emotion = detect_emotion(processed_text)
    phi_result = analyze_healthcare_entities(processed_text, target_language="en")

    # 症狀維持 list[dict]，方便下游泾用既有制式
    entities = phi_result.get("entities", [])
    symptoms = [
        entity for entity in entities if entity.get("category") == "SymptomOrSign"
    ]

    return {
        "entry": entry,
        "emotion": emotion,
        "symptoms": symptoms,
        "phi": phi_result,
    }

# processor.py 現在僅負責單筆日記的 AI 呼叫與簡單整理，
# 將較複雜的 PHI -> 前端格式化邏輯移至 diary.analysis