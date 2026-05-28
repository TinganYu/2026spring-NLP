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
    "藥劑": [
        {   
        "藥名": "...",
        "劑量": [...],
        "頻率": [...],
        "註記": [...]
        },
        ...
    ]
    
}

字典2格式:
{
    "藥名1": "學術說法1",
    "藥名2": "學術說法2",
    ...
}
'''

from shared.phi import analyze_healthcare_entities

class MedicationData:
    def __init__(self, name: str):
        self.name = name
        self.dosage = set()
        self.frequency = set()
        self.notes = set()

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "藥名": self.name,
            "劑量": list(self.dosage),
            "頻率": list(self.frequency),
            "註記": list(self.notes)
        }

def call_phi_service(text: str) -> dict:
    # 取得phi的分析結果
    phi_response = analyze_healthcare_entities(text)

    '''
    # 印出關係資訊
    relarions = phi_response['relations']
    for relation in relarions:
        print(f"Relation: {relation['relation_type']}")
        for role in relation['roles']:
            print(f"  Name: {role['name']} - Text: {role['entity_text']}")
    '''
    
    # 初始化用來分類儲存的字典（使用 set 可以自動去重）
    dict1 = {
        "病名": set(),
        "症狀": set(),
        "藥劑": []
    }

    # 學術名稱對應表
    normal_name = {}

    med_obj_map = {}

    # 遍歷 Azure 的實體結果，根據類別進行分類
    for entity in phi_response["entities"]:
        azure_cat = entity["category"]# 抓類別
        azure_text = entity["text"]# 抓文字

        if azure_cat == "Diagnosis":
            dict1["病名"].add(azure_text)
        elif azure_cat == "SymptomOrSign":
            dict1["症狀"].add(azure_text)
        elif azure_cat == "MedicationName":
            medication = MedicationData(azure_text)
            med_obj_map[azure_text] = medication
            dict1["藥劑"].append(medication)
            normal_name[azure_text] = entity["normalized_text"] # 回傳藥名的學術說法

    # 定義 Azure 關係類型與 Class 屬性的對應
    relation_mapping = {
        "DosageOfMedication": "dosage",
        "FrequencyOfMedication": "frequency",
        "RouteOfMedication": "notes",
        "DirectionOfMedication": "notes"
    }

    # 根據 relations 去補充已存在物件的資訊
    for relation in phi_response["relations"]:
        rel_type = relation["relation_type"]
        
        if rel_type in relation_mapping:
            target_attr = relation_mapping[rel_type]
            
            med_text = None
            attr_text = None
            
            for role in relation["roles"]:
                if role["name"] == "Medication":
                    med_text = role["entity_text"]
                else:
                    attr_text = role["entity_text"]
            
            # 如果成功找到藥名與屬性值，且該藥名在前面已經建立過物件
            if med_text and attr_text and (med_text in med_obj_map):
                # 根據藥名找到剛才丟進 list 的同一個物件，並把資訊填進去
                getattr(med_obj_map[med_text], target_attr).add(attr_text)
    
    #  資料整理 (將 Set 轉為 List，並將 Class 物件轉成字典格式)
    dict1["病名"] = list(dict1["病名"])
    dict1["症狀"] = list(dict1["症狀"])
    dict1["藥劑"] = [med_obj.to_dict() for med_obj in dict1["藥劑"]]

    return dict1, normal_name
   

if __name__ == "__main__":
    test_text = "Hello Patricia Taylor, let's confirm your emergency contact number is 555-987-6543. Your knee X-rays show clear Osteoarthritis. To manage the pain, take Celecoxib 200mg once daily with food."
    target_items, normal_name = call_phi_service(test_text)
    print("病名:", target_items["病名"])
    print("症狀:", target_items["症狀"])
    for med in target_items["藥劑"]:
        print("藥名:", med["藥名"])
        print("劑量:", med["劑量"])
        print("頻率:", med["頻率"])
        print("註記:", med["註記"])
    #print(target_items)
    print(normal_name)
