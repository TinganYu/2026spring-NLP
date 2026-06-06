from pymongo import MongoClient
db, client = None, None

# 連接 database
def connect():
    global client, db
    
    client = MongoClient(host='localhost',port=27017)
    db = client.NLP_FinalProject
    print("[DATABASE] Connected.")
    return

# 斷連 database
def disconnect():
    client.close()
    print("[DATABASE] Disconnected.")
    return

# 存入 diary 分析資料
def diary_insert(text, diary_record):
    # copy再存，避免insert時對 dict 加入 _id 欄位
    insert_data = diary_record.copy()
    insert_data["text"] = text
    db.diary.insert_one(insert_data)
    
    print("[DATABASE] Inserted diary record complete.")
    return

# 在 diary table 中尋找資料
def diary_find(select_dict = None):
    # select_dict: 尋找符合哪些條件的資料
    # 沒有設定條件就回傳所有資料
    if not select_dict:
        result = db.diary.find({}, {"_id": 0})
    else:
        result = db.diary.find(select_dict, {"_id": 0})
        
    print(f"[DATABASE] Select diary record with Condition: {select_dict}.")
    return result

# 存入 medical 分析資料
def medical_insert(medical_record):
    insert_data = medical_record.copy()
    db.medical.insert_one(insert_data)
    
    print("[DATABASE] Inserted medical record complete.")
    return

# 在 medical table 中尋找資料
def medical_find(select_dict = None):
    # select_dict: 尋找符合哪些條件的資料
    # 沒有設定條件就回傳所有資料
    if not select_dict:
        result = db.medical.find({}, {"_id": 0})
    else:
        result = db.medical.find(select_dict, {"_id": 0})
        
    print(f"[DATABASE] Select medical record with Condition: {select_dict}.")
    return result

# 回傳 start date ~ end date 的所有 diary data
def date_period_select(start, end):
    return diary_find({"date": {"$gte": start, "$lte": end}})
