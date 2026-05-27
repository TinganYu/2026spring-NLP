import sys
import os
# 將 2026-NLP路徑 設為import時搜尋的第一順位
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import configparser
from flask import Flask, request, abort, render_template, url_for, Blueprint, jsonify
import website.database as db

from diary.processor import process_entry
from shared.pii import review_pii
from diary.analysis import to_diary_record
from diary.aggregator import aggregate_weekly_records 
from diary.groq import summarize_health_trend, build_weekly_groq_payload

from medical.service_translate import call_translate_service
from medical.service_phi import call_phi_service
from medical.service_speech import speech_to_text


# Config Parser
config = configparser.ConfigParser()
config.read("config.ini")

UPLOAD_FOLDER = "website"

app = Flask(__name__)
app.json.sort_keys = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# @app.route("/api/entity-mapping/<entity_id>", methods=["GET"]) # 之後如果有做需要entity標籤的東西才會需要，請無視
# def get_entity_mapping(entity_id):
#     # 從數據庫取得完整的entity數據(尤其是data sources)
#     # 之後建好再加入程式
#     pass

@app.route("/api/weekly_dashboard", methods=["GET"])
def get_weekly_dashboard():
    user_id = request.args.get("user_id")
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date")
    
    # 從 DB 取出時間範圍內的日記（AnalysisResult 格式）
    analysis_records = db.get_diaries_by_range(user_id, start_date, end_date)
    
    # 直接聚合生成圖表
    dashboard_payload = aggregate_weekly_records(analysis_records)
    groq_payload = build_weekly_groq_payload(dashboard_payload)
    ai_summary = summarize_health_trend(groq_payload)

    print("[GET] Weekly Dashboard Summary:")
    print(ai_summary)

    return jsonify({
        "weekly_dashboard": dashboard_payload,
        "groq_summary": ai_summary,
    })

# 接收前端送來的日記內容，並回傳分析結果
@app.route("/diary_process", methods=["POST"])
def process_diary():
    if request.method == "POST":
        print("[POST] Diary Process POST, received data:", request.form)
        
        # 取出前端傳來的資料
        data = request.form
        date = data["date"] 
        text = data["message"] 
        meta = None 
        
        # 取得資料並處理
        result = process_entry(text, meta)  # AnalysisResult dict
        diary_record_view = to_diary_record(result, date)
        diary_record_view["symptoms"] = [
            symptom 
            for symptom in diary_record_view["symptoms"] 
            if symptom["status"] != "negated" and symptom["status"] != "other_person"]
        
        # 翻譯資料以供顯示
        target = "zh-Hant"
        for symptom in diary_record_view["symptoms"]:   # 翻譯症狀
            # 如果沒有 key 就顯示 display，只保留翻譯結果
            if not symptom["key"]:
                symptom["key"] = symptom["display"]
            del symptom["display"]
            
            symptom["key"] = call_translate_service(symptom["key"], target)['translations'][0]['text']
            
            # 翻譯所有時間跟頻率，只保留翻譯結果
            for i in range(len(symptom['times'])):
                symptom['times'][i] = call_translate_service(symptom['times'][i], target)['translations'][0]['text']
                
            for i in range(len(symptom['frequencies'])):
                symptom['frequencies'][i] = call_translate_service(symptom['frequencies'][i], target)['translations'][0]['text']
        
        for medication in diary_record_view["medications"]: # 翻譯用藥
            # 如果沒有 key 就顯示 display，保留原文跟翻譯結果
            if not medication["key"]:
                medication["key"] = medication["display"]
            del medication["display"]
            
            # [0]: 原文, [1]: 翻譯結果
            medication["key"] = [medication["key"]]
            medication["key"].append(call_translate_service(medication["key"][0], target)['translations'][0]['text'])
            
            # 翻譯所有時間跟頻率，只保留翻譯結果
            for i in range(len(medication['dosages'])):
                medication['dosages'][i] = call_translate_service(medication['dosages'][i], target)['translations'][0]['text']
                
            for i in range(len(medication['frequencies'])):
                medication['frequencies'][i] = call_translate_service(medication['frequencies'][i], target)['translations'][0]['text']
        
        # 存 diary data 到 DB
        db.diary_insert(text, diary_record_view)
        print("Diary Record View:", diary_record_view)    
        return jsonify(diary_record_view)

#接收前端送來的醫囑內容，並回傳分析結果
@app.route("/medical_process", methods=["POST"])
def process_medical():
    if request.method == "POST":
        print("[POST] Medical Process POST, received data:", request.form)
        
        # 取出前端傳來的資料
        data = request.form
        text = data["message"]
        target_lang = data["language"]
        
        # 翻譯醫囑
        text_translated = call_translate_service(text, target_lang)
        
        # 偵測醫囑PHI
        phi, medicine = call_phi_service(text)
        
        #給所有PHI翻譯成中文，並把翻譯加入 phi(dict)
        for key, value in phi.items():
            tmp = {"original": value, "translated": []}
            for i in value:
                tmp["translated"].append(call_translate_service(i, target_lang)["translations"][0]["text"])
            phi[key] = tmp
        
        # 回傳結果給前端
        result = {
            "original_text": text,
            "translated_text": text_translated['translations'][0]['text'],
            "phi": phi
        }
        print("Medical Result:", result)
        return jsonify(result)
 
# 執行語音錄入並回傳錄入文字   
@app.route("/speech_to_text", methods=["POST"])
def speech():
    result = speech_to_text()
    return jsonify(result)

#接收前端送來的內容，並回傳PII審核結果
@app.route("/pii_review", methods=["POST"])
def diary_pii_review():
    print("[POST] PII Review POST, received data:", request.form)
    
    # 取出前端傳來的資料
    text = request.form
    text = text['text']
    
    # PII偵測並回傳
    review = review_pii(text) 
    print("PII Review Result:", review)
    return jsonify(review)

@app.route("/history_get", methods=["POST"])
def db_select():
    print("[POST] History Get POST, received data:", request.form)
    
    # 取出前端傳來的資料
    text = request.form
    database = text["class"]

    # 搜尋對應 database 中的所有資料
    if database == "diary":
        # 資料按照日期
        result = db.diary_find()
        result.sort("date",-1)
    elif database == "medical":
        result = db.medical_find()
    else:
        return None
    
    result = list(result)
    return jsonify(result)

#一打開網站要做的事情
@app.route("/")
def home():
    print("[GET] Home GET")
    return render_template("diary.html")

#前往情緒日記頁面
@app.route("/diary")
def diary():
    return render_template("diary.html")

#前往醫囑頁面
@app.route("/medical")
def medical():
    return render_template("medical.html")

#前往圖表頁面
@app.route("/graph")
def graph():
    return render_template("graph.html")

if __name__ == "__main__":
    db.connect()
    app.run()