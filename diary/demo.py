"""示範用的 CLI/runner：模擬使用者輸入並顯示 `process_entry` 的輸出。

供本地快速驗證處理流程與輸出格式使用。
"""
# 這是一個簡單的示範程式，模擬使用者輸入日記內容並將其傳遞給處理器，最後以 JSON 格式輸出結果。
import json
from dataclasses import asdict

from .processor import process_entry


def run_demo(user_input: str):
    """Simulate user input passed to the processor and print JSON result."""
    res = process_entry(user_input, meta={"source": "demo"})
    # Convert dataclasses to dict for JSON serialization
    obj = asdict(res)
    print(json.dumps(obj, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # 模擬使用者輸入（你可以修改這個變數）
    user_input = "今天覺得頭暈，有點難過，但吃了藥有比較好。今天遇到王曉明心情大好!"
    run_demo(user_input)
