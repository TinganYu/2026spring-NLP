# 資料流程

## 概述

本專案使用混合管道：

1. **PII**: 偵測並遮蔽敏感個人資訊。
2. **翻譯**: 必要時將日記文本翻譯成英文。
3. **PHI**: 從文本中提取醫療保健實體及其關聯。
4. **情緒**: 偵測情緒/感受。
5. **分析**: 總結關聯及趨勢，提供使用者友善的輸出。
6. **Groq**: 根據結構化 JSON 生成自然語言的週/月摘要。

## 建議的日記條目流程

- 接收使用者輸入的文本
- PII 審查
- 根據使用者選擇進行選擇性遮蔽
- 若源文本為中文，翻譯成英文
- 對英文文本執行 PHI 提取
- 執行情緒偵測
- 將結構化 JSON 儲存到資料庫
- 稍後，將聚合的 JSON 發送給 Groq 以生成評論文本

## 建議的醫囑流程

- 接收醫囑文本
- PII 審查
- 根據使用者選擇進行選擇性遮蔽
- 醫囑已為英文，無需翻譯
- 直接執行 PHI 提取
- 將結構化 JSON 儲存到資料庫

## Groq 使用方式

Groq 不應用於原始提取。
應該用於：

- 週趨勢摘要
- 月度評論摘要
- 相關性解釋
- 醫生就診準備摘要


## 日記檔案說明
1. `processor.py`：負責 per-entry 的處理（情緒偵測 + PHI），並把標準化結果放到 AnalysisResult.extra['phi'] 與 AnalysisResult.symptoms（單一症狀來源）。
2. `analysis.py`：像 build_correlation_discovery、build_doctor_visit_prep 這類較詳細或耗時的 PHI 摘要保留為 on‑demand 呼叫（由後端在使用者請求時或 UI 按鈕觸發時執行），不會在每次 process 時同步產生。
3. `aggregator.py`：負責從多筆 AnalysisResult 聚合週級資料，會呼叫  `visualization.py` 的函式產生前端直接可用的 chart payload（labels/series/ranking 等）。
4. `visualization.py`：只把 canonical extra['phi'] 轉成圖表 payload；已移除把完整 relations 塞入 markers 的做法，前端收到的是精簡的繪圖欄位，不含原始 PHI blob。