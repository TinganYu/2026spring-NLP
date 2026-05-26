# 2026-NLP
# 🏥 Medical Order Intelligence Assistant  
### 智慧醫囑理解與病患照護輔助平台

自然語言處理（NLP）期末專案

---

## 📖 Project Overview

這個專案是目前實際可運作的醫療 NLP 原型，重點放在兩條主線：

1. 醫囑分析：將醫囑內容翻譯、結構化，並提取醫療實體與關係。
2. 日記分析：分析病患日記中的情緒、症狀、用藥與時序變化，再產出圖表與 Groq 白話摘要。

---

## ✅ 目前實作的功能

### 1. Medical Process（醫囑分析）

目前醫囑流程會做以下事情：

- 接收前端輸入的醫囑文字
- 進行 PII 審核與遮蔽
- 透過翻譯服務處理多語言輸出
- 使用 PHI / healthcare entity extraction 取得醫療實體與關係
- 回傳結構化 JSON 給前端與資料庫

對應的主要檔案：

- `website/app.py`
- `medical/service_translate.py`
- `medical/service_phi.py`
- `shared/pii.py`

### 2. Diary Process（日記分析）

目前日記流程會做以下事情：

- 接收病患日記內容
- 進行情緒偵測
- 進行 PHI / 症狀與藥物實體分析
- 轉成前端與資料庫可用的 `DiaryRecord`
- 存入資料庫

對應的主要檔案：

- `diary/processor.py`
- `diary/analysis.py`
- `diary/models.py`

### 3. Weekly Dashboard + Groq Summary

日記資料累積後，系統會：

- 由 `aggregator.py` 彙整週報資料
- 由 `visualization.py` 產生圖表 payload
- 由 `groq.py` 把週報資料轉成一段白話摘要
- 由 `website/app.py` 一次回傳圖表與摘要給前端

對應的主要檔案：

- `diary/aggregator.py`
- `diary/visualization.py`
- `diary/groq.py`
- `website/app.py`

### 4. Privacy Protection（PII 保護）

系統支援輸出端 PII 審核，用來遮蔽電話、姓名等敏感資訊，適合分享給家屬或做截圖展示。

### 5. Visualization（視覺化）

系統會將日記分析結果轉成圖表資料，目前包含：

- 情緒折線圖
- 症狀頻率圖
- 用藥頻率圖
- 情緒-症狀共現圖
- 症狀時間軸
- 用藥時間軸
- 週曆熱力圖
- 情緒×症狀熱力圖

詳細圖表說明請見 [diary/README.md](diary/README.md)。

---

## 🧩 Project Structure

目前實際使用的核心模組如下：

```text
website/
├── app.py
├── database.py
├── templates/
└── static/

diary/
├── processor.py
├── analysis.py
├── aggregator.py
├── visualization.py
├── groq.py
├── emotion.py
├── models.py
└── demo.py

medical/
├── service_translate.py
├── service_phi.py
└── service_speech.py

shared/
├── pii.py
├── translate.py
└── phi.py

```

---

## 🔧 Technologies

- Python
- Flask
- Azure AI Language / Health Text Analytics
- Groq
- MongoDB
- JavaScript / jQuery

