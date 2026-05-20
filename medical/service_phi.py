'''
利用phi取得資料分析，
再從中萃取出病名、症狀、藥名、劑量、頻率、註記等資訊，
並回傳藥名的學術說法（normalized_text)

輸入: 原始文章(original_text)
輸出: 字典1(包含所需資訊)、字典2(藥名的學術說法)

字典1格式:
{
    "病名": [...],
    "症狀": [...],
    "藥名": [...],
    "劑量": [...],
    "頻率": [...],
    "註記": [...]
}

字典2格式:
{
    "藥名1": "學術說法1",
    "藥名2": "學術說法2",
    ...
}
'''

from shared.phi import analyze_healthcare_entities

def call_phi_service(text: str) -> dict:
    phi_response = analyze_healthcare_entities(text)

    # 初始化用來分類儲存的字典（使用 set 可以自動去重）
    extracted_data = {
        "病名": set(),
        "症狀": set(),
        "藥名": set(),
        "劑量": set(),
        "頻率": set(),
        "註記": set()
    }

    # 定義 Azure 欄位與目標項目的對映關係
    category_mapping = {
        "Diagnosis": "病名",
        "SymptomOrSign": "症狀",
        "MedicationName": "藥名",
        "Dosage": "劑量",
        "Frequency": "頻率",
        # 將「用藥途徑」與「醫囑方向」歸類在「註記」中
        "MedicationRoute": "註記",
        "Direction": "註記" 
    }

    for entity in phi_response["entities"]:
        azure_cat = entity["category"]
        azure_text = entity["text"]

        # 如果這個類別在對映表內，就分類放進去
        if azure_cat in category_mapping:
            target_key = category_mapping[azure_cat]
            extracted_data[target_key].add(azure_text)

            normal_name = {}
            # 回傳藥名的學術說法
            if target_key == "藥名":
                normal_name[azure_text] = entity["normalized_text"]

        #print(f"Category: {entity['category']}, Text: {entity['text']}")
    
    # 將 set 轉換回 list 方便後續檢視
    return {k: list(v) for k, v in extracted_data.items()}, normal_name
   

if __name__ == "__main__":
    test_text = "Hello Ms. Sarah Jenkins, your date of birth is August 22, 1995, correct? Based on your symptoms, I've diagnosed you with Bronchial Asthma. For your treatment, you need to inhale Albuterol 90mcg, that's 2 puffs, every 4 hours as needed for wheezing."
    target_items, normal_name = call_phi_service(test_text)
    #print(target_items)
    print(normal_name)
