# Groq 整合備註

## 用途

Groq 用於將結構化健康資料轉換成自然語言摘要。
應該用於：

- 週評論文本
- 月度趨勢摘要
- 相關性解釋
- 醫生就診準備摘要

## 輸入格式

Groq 應接收結構化 JSON，例如：

```json
{
  "emotion_trend": [
    {"date": "2026-05-01", "emotion_label": "negative", "emotion_score": 0.82}
  ],
  "symptom_trend": [
    {"date": "2026-05-01", "symptom_or_sign": ["頭痛"]}
  ],
  "phi_summary": {
    "relation_facts": [
      {"relation_type": "TimeOfCondition", "text": "頭痛發生在今天"}
    ]
  }
}
```

## 預期輸出

Groq 應生成友善的中文摘要，而非原始實體提取。

## 檔案位置

- `diary/groq.py`: Groq API 包裝程式
- `docs/data_flow_zh.md`: 管道說明
- `docs/data_dictionary_zh.md`: 資料庫欄位指南
