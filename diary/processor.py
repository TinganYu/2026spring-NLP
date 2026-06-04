"""Per-entry processing: 以單筆日記文本產生標準化的 `AnalysisResult`。

職責：偵測情緒、呼叫 PHI 分析、回傳可存入 DB 的結構化結果。
processor.py 現在僅負責單筆日記的 AI 呼叫與簡單整理，
將較複雜的 PHI 分析 -> 前端格式化邏輯移至 diary.analysis
"""
from .models import DiaryEntry, AnalysisResult
from .emotion import detect_emotion
from shared.phi import analyze_healthcare_entities

# 最主要的 function：把單筆日記文本轉成 AnalysisResult
def process_entry(text: str, meta: dict = None) -> AnalysisResult:
    """Orchestrator: receives a diary text and returns structured analysis."""
    processed_text = text

    entry: DiaryEntry = {"text": processed_text, "meta": meta or {}}
    emotion = detect_emotion(processed_text)
    phi_result = analyze_healthcare_entities(processed_text, target_language="en", source_language="zh-Hant") # 這邊預告會需要翻譯成英文

    # 額外將症狀抓出來
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

