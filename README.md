# 2026-NLP
# 🏥 Medical Order Intelligence Assistant  
### 智慧醫囑理解與病患照護輔助平台

自然語言處理（NLP）期末專案

---

# 📖 Project Overview

Medical Order Intelligence Assistant 是一套結合醫療 NLP、情緒分析與隱私保護的智慧醫療輔助系統，目標是協助病患與照護者更容易理解醫囑內容，並透過日記分析觀察症狀與情緒變化趨勢。

本系統聚焦於：

- 將非結構化醫囑整理成病患較容易閱讀的結構化資訊
- 提供病患可理解的白話醫療摘要
- 分析病患居家日記中的情緒與症狀
- 建立藥物與症狀變化的時序關聯
- 提供輸出端的隱私保護機制
- 支援多語言醫囑輸出

---

# ✨ Core Features

## 1. Medical Order NLP Analysis

系統可對英文醫囑進行醫療 NLP 分析，包含：

### 🔹 Named Entity Recognition (NER)

辨識醫療實體，例如：

- Medication（藥物）
- Symptom（症狀）
- Diagnosis（診斷）
- Anatomy（解剖部位）

---

### 🔹 Medical Information Structuring

系統會將原本難閱讀的醫囑內容整理成較清楚的表格化資訊。

範例：

原始醫囑：

```text
Take Aspirin 100mg twice daily after meals
```

整理後：

| Medication | Dosage | Frequency | Note |
|---|---|---|---|
| Aspirin | 100mg | twice daily | after meals |

此功能主要是為了：

- 提升病患閱讀性
- 協助快速理解醫囑
- 方便後續分析與顯示

---

### 🔹 Optional Advanced NLP Features

若時間允許，系統可能進一步加入：

- Assertion Detection（否定與不確定語意分析）
- Entity Linking（ICD-10 / UMLS 醫療代碼連結）

例如：

| Type | Example |
|---|---|
| Positive | chest pain |
| Negative | no chest pain |
| Uncertain | possible chest pain |

> 此部分目前為進階功能，可能依開發進度調整。

---

## 2. Plain-Language Medical Summarization

系統會將專業醫療資訊轉換成病患可理解的白話說明。

### 🔹 Wikipedia-based Explanation

系統會先從醫囑中提取藥物名稱，再透過 Wikipedia API 取得相關藥物介紹內容。

例如：

```text
Metformin
```

系統會自動抓取 Wikipedia 上與 Metformin 相關的醫療介紹文字。

---

### 🔹 AI Summarization

取得 Wikipedia 內容後，系統會進一步：

- 擷取前 200 字重點內容
或
- 使用 Azure AI Summarization 功能生成摘要

將原本複雜的醫療說明轉換為病患更容易理解的短文。

範例：

```text
Metformin is commonly used to control blood sugar levels in diabetes patients.
```

可能轉換為：

```text
這個藥物主要用於幫助控制血糖。
```

---

### 🔹 Feature Goal

此功能主要希望：

- 降低醫療術語閱讀門檻
- 協助病患理解醫囑
- 提升醫病溝通效率
- 提供較易閱讀的藥物資訊

---

# 📔 Diary & Symptom Analysis

除了醫囑分析外，系統也支援病患日記分析。

## 🔹 Emotion Analysis

分析日記中的情緒傾向：

- Positive
- Neutral
- Negative

並輸出情緒分數。

---

## 🔹 Symptom Keyword Detection

使用中文症狀詞表進行比對，例如：

- 頭暈
- 胸痛
- 噁心
- 咳嗽

藉此統計症狀出現頻率。

---

## 🔹 Trend Correlation

系統可觀察：

- 症狀頻率變化
- 情緒變化
- 換藥時間點

協助使用者觀察：

> 症狀是否在特定藥物調整後改善。

---

# 🌐 Multi-language Support

系統提供多語言輸出功能，協助外籍照護者閱讀醫療資訊。

目前規劃支援：

- 繁體中文
- English
- Tiếng Việt
- Bahasa Indonesia

多語言功能主要定位於：

> 「輸出端翻譯」

而非多語言輸入。

---

# 🔒 Privacy Protection

本系統重視病患隱私，提供輸出端 PII 保護機制。

可遮蔽內容包含：

- 姓名
- 電話
- 地址
- 病歷號碼

範例：

```text
王小明 → [患者]
0912-345-678 → [聯絡資訊]
```

此功能適合：

- 截圖分享
- 家屬傳閱
- 非正式醫療討論

---

# 📊 Visualization

系統可將分析結果視覺化呈現，例如：

- 情緒變化折線圖
- 症狀頻率圖
- 藥物介入時間點標記

幫助使用者更直觀理解健康變化趨勢。

---

# 🏗️ System Architecture

```text
User Input
   │
   ▼
Medical Order / Diary Text
   │
   ▼
Medical NLP Analysis
   │
   ├── Entity Recognition
   ├── Medical Structuring
   ├── Medical Summarization
   └── (Optional) Assertion / Entity Linking
   │
   ▼
Diary Analysis
   │
   ├── Emotion Analysis
   ├── Symptom Detection
   └── Trend Correlation
   │
   ▼
Database Storage
   │
   ▼
Visualization & Multi-language Output
```

---

# 🛠️ Technologies

## NLP & AI

- Azure AI Language
- Azure Health Text Analytics
- Azure AI Summarization
- Wikipedia API
- NLP Pipeline

## Backend

- Python
- PostgreSQL

## Frontend

- Chart.js
- Web UI

---

# 📦 Future Improvements

以下功能為未來可擴充方向：

- PDF 醫療摘要報告
- 更完整的醫療知識庫
- 更進階的症狀關聯分析
- FHIR 格式輸出
- Longitudinal patient tracking
- 多病患管理系統

---

# 🎯 Project Goal

本專題希望展示：

> NLP 不只是文字分析工具，
> 而是能夠真正協助病患理解醫療資訊、提升照護溝通品質的智慧醫療應用。

同時也希望探索：

- 醫療 NLP
- 隱私保護
- 多語言醫療資訊
- 症狀時序分析

在實際醫療輔助場景中的整合可能性。