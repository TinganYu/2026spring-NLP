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

def diary_insert():
    #alloc_tmp = {'name':tmp,'chr1':c[0]['_id'],'chr2':c[1]['_id'],'chr3':c[2]['_id']}
    #db.allocations.insert_one(alloc_tmp)
    pass

def diary_find():   
    # db.materia_func.find({'type':type})
    pass

def medical_insert():
    pass

def medical_find():
    pass