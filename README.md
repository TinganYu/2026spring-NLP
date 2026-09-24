# 2026-NLP
# Medical Order Intelligence Assistant  
### 智慧醫囑理解與病患照護輔助平台

自然語言處理（NLP）期末專案

---

## 目錄

- [Project Overview](#project-overview)
- [Azure AI Language 整合](#azure-ai-language-整合)
- [目前實作的功能](#目前實作的功能)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [安裝與啟動](#安裝與啟動)
- [Demo 影片](#demo-影片)
- [PPT 簡報](#ppt-簡報)

## Project Overview

這個專案是目前實際可運作的醫療 NLP 原型，重點放在兩條主線：

1. 醫囑分析：將醫囑內容翻譯、結構化，並提取醫療實體與關係。
2. 日記分析：分析病患日記中的情緒、症狀、用藥與時序變化，再產出圖表與 Groq 白話摘要。

---

## Azure AI Language 整合

本專案結合 Azure AI Language 服務，將自然語言醫療文字轉換成可供系統使用的結構化資料，主要用途包括：

- 使用 Health Text Analytics 擷取疾病、症狀、藥物等醫療實體。
- 分析醫療實體之間的關係，協助建立醫囑與病患狀態的關聯。
- 搭配 Azure AI Translator 處理多語言醫療文字。
- 搭配 Azure AI Speech 將語音輸入轉換成文字，再交由後續 NLP 流程分析。

相關服務程式位於 `medical/` 與 `shared/`。執行專案時，請在自己的設定檔中填入 Azure 與其他服務所需的金鑰和端點；這些資訊不會放在公開的程式碼裡。

---

## 目前實作的功能

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

系統會將日記分析結果轉成圖表資料，目前健康趨勢頁面包含 4 張圖表：

- 情緒波動曲線：依日期顯示情緒指數變化的折線圖。
- 症狀次數統計：統計最常出現症狀的長條圖。
- 用藥次數統計：統計用藥頻率的長條圖。
- 情緒與症狀共現分析：以正負情緒區分，呈現情緒與症狀同日出現次數的堆疊長條圖。

詳細圖表說明請見 [diary/README.md](diary/README.md)。

---

## Project Structure

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

## Technologies

- Python
- Flask
- Azure AI Language / Health Text Analytics
- Azure AI Translator
- Azure AI Speech
- Groq
- MongoDB
- JavaScript / jQuery

---

## 安裝與啟動

### 安裝套件

```bash
pip install -r requirements.txt
```

### 設定服務金鑰

請依照 `config.ini` 的區段設定 Azure AI Language、Azure Translator、Azure Speech、Groq 與 MongoDB 所需的金鑰、端點及連線資訊。公開專案時，請改用環境變數或本機設定檔，避免將機密資訊提交至 GitHub。

### 啟動 Flask 應用程式

```bash
python website/app.py
```
---

## Demo 影片

[觀看 DEMO 影片](https://drive.google.com/file/d/1Ylc3xaeN3OgpD6YX5r3e8lXuNM8CL_Rm/view?usp=sharing)

## PPT 簡報

[查看專題簡報](https://canva.link/h9wtrbf3ot15zj4)

