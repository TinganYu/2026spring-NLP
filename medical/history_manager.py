'''
將翻譯紀錄留存
輸入: 原始文字(original_text)、翻譯後文字(translated_text)、實體識別結果(entities)
輸出: 無（將紀錄儲存到 JSON 檔案中）
'''

import json
import os
from datetime import datetime
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

HISTORY_FILE = config.get("HISTORY", "HISTORY_FILE")
MAX_HISTORY_COUNT = config.getint("HISTORY", "MAX_HISTORY_COUNT")

def save_to_history(original_text: str, translated_text: str, entities: dict):
    """儲存一筆醫囑紀錄到 JSON 檔案"""
    history = load_history()
    
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original": original_text,
        "translated": translated_text,
        "entities": entities
    }
    
    # 插入到最前面 (最新的一筆)
    history.insert(0, new_entry)
    
    # 限制最多 30 筆
    if len(history) > MAX_HISTORY_COUNT:
        history = history[:MAX_HISTORY_COUNT]
        
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def load_history() -> list:
    """讀取所有歷史紀錄"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
    