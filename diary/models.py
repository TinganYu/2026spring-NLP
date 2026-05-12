from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class DiaryEntry:
    text: str
    meta: Dict[str, Any]


@dataclass
class SentenceResult:
    text: str
    label: str
    score: float


@dataclass
class EmotionResult:
    label: str
    score: float
    sentences: Optional[List[Dict[str, Any]]] = None


@dataclass
class AnalysisResult:
    entry: DiaryEntry
    emotion: EmotionResult
    symptoms: List[Dict[str, Any]]
    extra: Dict[str, Any] = None
