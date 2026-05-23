from pymongo import MongoClient
db, client = None, None

def connect():
    global client, db
    
    client = MongoClient(host='localhost',port=27017)
    db = client.NLP_FinalProject
    return

def disconnect():
    client.close()
    return

def diary_insert(entry, diary_record):
    insert_data = diary_record.copy()
    insert_data["text"] = entry["text"]
    #alloc_tmp = {'name':tmp,'chr1':c[0]['_id'],'chr2':c[1]['_id'],'chr3':c[2]['_id']}
    db.diary.insert_one(insert_data)
    print("[DATABASE] Inserted diary record complete.")
    return

def diary_find():   
    # db.materia_func.find({'type':type})
    return

def medical_insert():
    return

def medical_find():
    return