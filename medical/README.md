# Medical資料夾內檔案介紹
用來實作醫囑系統的功能

## 醫囑系統功能
1. 使用者輸入醫囑(打字、開啟語音)
2. 醫囑翻譯
3. 對PHI給的資料分析取得所需
4. 根據藥名去抓Wiki的連結
5. 歷史醫囑紀錄清單(顯示日期，最多30筆)

## 主要檔案
`service_speech.py` : 語音轉文字

`service_translate.py` : 利用shared資料夾內的`translate.py`翻譯

`service_phi.py` : 利用shared資料夾內的`phi.py`分析，並取得所需資訊

`wiki_utils.py` : 用藥名去找維基百科的連結

`history_manager.py` : 紀錄翻譯和過濾後的phi資訊

## 建議使用
請參考`test.py`

每個.py檔前面都有介紹該檔案的作用和輸入輸出
