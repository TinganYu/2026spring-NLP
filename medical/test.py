'''
測試整合所有服務的流程

輸入: 無（直接從麥克風錄音)
=> 若是手動輸入，可以跳過speech_to_text()，直接給定原始文字
'''

from service_translate import call_translate_service
from service_phi import call_phi_service
from wiki_utils import get_wiki_info
from service_speech import speech_to_text
from history_manager import save_to_history, load_history
import json

# 本地終端機直接測試
if __name__ == "__main__":
    original = speech_to_text()
    translated = call_translate_service(original, "id")["translations"][0]["text"]
    entities, normal_name = call_phi_service(translated)
    for drug in entities["藥名"]:
        if drug in normal_name:
            drug = normal_name[drug]  # 使用學術名稱查詢維基百科
        wiki_info = get_wiki_info(drug)
        print(f"{drug} 的維基百科連結: {wiki_info}")
    save_to_history(original, translated, entities)
    
    
    # 印出目前所有歷史紀錄
    history = load_history()
    print(json.dumps(history, ensure_ascii=False, indent=4))
    