# 圖表輸出

本專案可為前端產生圖表就緒的 JSON。

## 1. 情緒折線圖

使用此負載繪製日常情緒分數的折線圖。

範例輸出：

```json
{
  "chart_type": "line",
  "labels": ["2026-05-01", "2026-05-02"],
  "series": [
    {
      "name": "emotion_score",
      "label": "情緒分數",
      "type": "line",
      "data": [0.2, 0.6],
      "y_axis": "emotion"
    }
  ],
  "markers": [
    {
      "date": "2026-05-01",
      "emotion_label": "negative",
      "emotion_score": 0.2,
      "symptoms": ["頭痛"],
      "medications": ["布洛芬"],
      "relations": []
    }
  ]
}
```

## 2. 症狀頻率圖

使用此負載繪製症狀的長條圖或詞頻風格視覺化。

## 3. 用藥頻率圖

使用此負載繪製用藥提及次數的長條圖。

## 4. 情緒-症狀共現分析

使用此負載顯示相關性，例如：

- 負面情緒 + 頭痛
- 焦慮 + 失眠

## 前端備註

前端可直接使用返回的 JSON 搭配 Chart.js、ECharts 或其他視覺化庫。
