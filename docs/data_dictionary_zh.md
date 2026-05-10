# 資料字典

本文件說明應儲存重要資料的位置，以便資料庫擁有者能快速找到。

## 主要記錄表

建議表名稱：`entries`

- `id`: 主鍵
- `user_id`: 使用者識別碼
- `date`: 項目日期
- `source_type`: `diary`（日記）或 `medical_order`（醫囑）
- `original_text`: 原始使用者文本
- `masked_text`: 遮蔽 PII 後的文本
- `translated_text`: 翻譯後的文本（如適用）
- `sentiment_label`: 情緒標籤
- `sentiment_score`: 情緒信心分數
- `pii_json`: PII 審查結果，以 JSON 格式儲存
- `phi_json`: PHI 結果，以 JSON 格式儲存
- `analysis_json`: 相關性/趨勢摘要，以 JSON 格式儲存

## 為什麼儲存 JSON 欄位

- 日後輕鬆重新執行分析
- 輕鬆建立週/月摘要
- 輕鬆追蹤原始實體來自 Azure 哪一個服務
- 讓 Groq 層輕鬆從結構化資料生成報告

## 常見 PHI 類別要保留

- `SymptomOrSign`（症狀或體徵）
- `MedicationName`（藥物名稱）
- `Dosage`（劑量）
- `Frequency`（頻率）
- `RouteOfAdministration`（給藥途徑）
- `BodyStructure`（身體結構）
- `Diagnosis`（診斷）
- `ProcedureName`（程序名稱）
- `TestName`（測試名稱）
- `TreatmentName`（治療名稱）
- `Duration`（持續時間）
- `ConditionQualifier`（狀況限定詞）
