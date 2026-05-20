'''
使用Azure 翻譯服務，將使用者的文字翻譯成指定的語言
輸入: 原始文字(original_text)、目標語言(target_lang)
輸出: 翻譯後的文字結果
'''

from shared.translate import translate_text

def call_translate_service(text: str, target_lang: str):
    return translate_text(text, target_lang)