# diary 模組說明

這個資料夾放的是日記分析相關的核心邏輯，負責把單筆日記轉成結構化資料，再進一步整理成週報圖表與 AI 摘要。

## 主要職責

- `processor.py`：處理單筆日記，執行情緒偵測與 PHI 分析。
- `analysis.py`：把 PHI 結果整理成前端可直接使用的 `DiaryRecord`。
- `aggregator.py`：彙整多筆日記成週級資料，產生圖表用 payload。
- `visualization.py`：把彙整後的資料轉成圖表結構。
- `groq.py`：把週報資料轉成自然語言摘要。
- `demo.py`：本機示範流程與資料形狀。

## 資料流程

1. 使用者輸入日記。
2. `processor.py` 產生每筆 `AnalysisResult`。
3. `analysis.py` 轉成 `DiaryRecord`。
4. `aggregator.py` 聚合多筆資料，產生週報與圖表 payload。
5. `groq.py` 讀取週報資料，輸出一段白話摘要。
6. `website/app.py` 將圖表與摘要一起回傳給前端。

## 輸出重點

- 圖表資料由 `aggregator.py` 和 `visualization.py` 負責。
- AI 白話摘要由 `groq.py` 負責。
- 目前週報 API 會回傳兩個主要部分：
  - `weekly_dashboard`
  - `groq_summary`

## visualization 圖表介紹

`visualization.py` 會把整理好的 `DiaryRecord` 轉成前端可以直接畫圖的 payload。每個圖表的用途如下：

| 圖表函式 | chart_type | 內容說明 | 常見用途 |
|---|---|---|---|
| `build_emotion_line_chart` | `line` | 將每天的情緒分數轉成折線圖，負面情緒會顯示為負值、正面情緒會顯示為正值。`markers` 也會附上當日症狀與用藥。 | 看整體情緒趨勢、標出波動日 |
| `build_symptom_frequency_chart` | `bar` | 統計症狀/徵象出現次數，依照 `key` 或 `display` 做排行。 | 找出最常出現的症狀 |
| `build_medication_frequency_chart` | `bar` | 統計藥物提及次數，可選擇只算 `taken == True` 的藥物。 | 看常用藥物、觀察服藥頻率 |
| `build_emotion_symptom_cooccurrence` | `cooccurrence` | 統計情緒與症狀的同日共現次數，輸出情緒摘要、症狀摘要與 pair summary。 | 找出「情緒 + 症狀」的常見組合 |
| `build_symptom_timeline` | `timeline` | 將症狀依日期串成時間軸，連續日期且狀態相同會合併成同一段 span。 | 看症狀何時出現、持續多久、是否反覆 |
| `build_medication_timeline` | `timeline` | 將用藥依日期串成時間軸，區分連續記錄與分段紀錄。 | 看藥物使用區間與持續性 |
| `build_emotion_heatmap_calendar` | `calendar_heatmap` | 依日期生成週曆熱力圖，值由情緒極性換算而來。 | 快速看整段時間的情緒分布 |
| `build_cooccurrence_heatmap` | `heatmap` | 以情緒為 y 軸、症狀為 x 軸，建立共現矩陣。 | 看哪種情緒最常和哪些症狀一起出現 |

### 回傳資料結構

`build_health_dashboard_payload(records)` 會一次回傳完整儀表板，包含：

- `emotion_line_chart`
- `symptom_frequency_chart`
- `medication_frequency_chart`
- `cooccurrence_chart`
- `symptom_timeline`
- `medication_timeline`
- `emotion_heatmap_calendar`
- `cooccurrence_heatmap`

前端可以直接把這些欄位丟給 Chart.js、ECharts 或其他圖表庫。

## 開發時的注意事項

- 若要調整 assertion、症狀狀態或用藥推論，先看 `analysis.py` 與 `processor.py`。
- 若要改圖表欄位，先看 `visualization.py`。
- 若要改摘要口吻或摘要輸入格式，先看 `groq.py`。
- 若要調整 API 回傳結構，先看 `website/app.py`。

