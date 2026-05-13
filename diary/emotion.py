
import os
from .models import EmotionResult
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import configparser

# Config Parser: load from config.ini, fallback to environment variables
config = configparser.ConfigParser()
config.read("config.ini")


def _get_azure_setting(env_name: str, default: str = None) -> str:
    try:
        return config.get("AzureLanguage", env_name)
    except Exception:
        print(f"config.get failed for {env_name}")
        return os.getenv(env_name, default)


# Read settings (can be set in [AzureLanguage] section of config.ini)
_AZURE_KEY = _get_azure_setting("AZURE_LANGUAGE_KEY")
_AZURE_ENDPOINT = _get_azure_setting("AZURE_LANGUAGE_ENDPOINT")
_DEFAULT_LANGUAGE = _get_azure_setting("AZURE_LANGUAGE_DEFAULT", "zh")


# Initialize client if credentials available; otherwise leave None and use local fallback
text_analytics_client = None
if _AZURE_KEY and _AZURE_ENDPOINT:
    try:
        _credential = AzureKeyCredential(_AZURE_KEY)
        text_analytics_client = TextAnalyticsClient(endpoint=_AZURE_ENDPOINT, credential=_credential, default_language=_DEFAULT_LANGUAGE)
    except Exception:
        text_analytics_client = None


def detect_emotion(text: str) -> EmotionResult:
    """Perform sentence-level sentiment analysis using Azure and aggregate by confidence-weighted sum.

    Requires Azure client to be configured via `config.ini` or environment variables.
    """
    if not text_analytics_client:
        raise RuntimeError("Azure Text Analytics client is not configured. Please set Azure settings in config.ini or environment variables.")

    t = text or ""
    # Call Azure analyze_sentiment which includes sentence-level results
    resp = text_analytics_client.analyze_sentiment(documents=[t], language=_DEFAULT_LANGUAGE)
    doc = resp[0]

    totals = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    sentences_out = []
    for s in doc.sentences:
        lbl = s.sentiment # positive/neutral/negative
        scores = s.confidence_scores # confidence scores for each label
        sent_score = float(max(scores.positive, scores.neutral, scores.negative)) # 用最高的信心分數代表該句的情緒強度(我忘記azure是不是本來就只會輸出最高的)
        sentences_out.append({"text": s.text, "label": lbl, "score": sent_score})
        totals["positive"] += float(scores.positive) # 沒有直接丟棄較低的分數。它把每一句的「微量負向」或「微量中立」通通存起來，最後再看整體誰勝出。
        totals["neutral"] += float(scores.neutral)
        totals["negative"] += float(scores.negative)

    overall_label = max(totals, key=totals.get) # 整體情緒標籤由三個類別中分數最高的決定
    total_sum = sum(totals.values())
    overall_score = float(totals[overall_label] / total_sum) if total_sum > 0 else 0.0 # 整體情緒強度則是該類別的分數占總分的比例，這樣可以反映出在整體文本中該情緒的相對強度

    return EmotionResult(label=overall_label, score=overall_score, sentences=sentences_out)
