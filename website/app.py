import sys
import os
# 將 2026-NLP路徑 設為import時搜尋的第一順位
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
from datetime import datetime
from dateutil.relativedelta import relativedelta

import configparser
from flask import Flask, request, abort, render_template, url_for, Blueprint, jsonify
import website.database as db

from diary.processor import process_entry
from diary.analysis import to_diary_record
from diary.aggregator import aggregate_weekly_records 
from diary.groq import summarize_health_trend

from medical.service_phi import call_phi_service
from medical.service_speech import speech_to_text
from medical.wiki_utils import get_wiki_info

from shared.pii import review_pii
from shared.translate import translate_to


# Config Parser
config = configparser.ConfigParser()
config.read("config.ini")

UPLOAD_FOLDER = "website"

app = Flask(__name__)
app.json.sort_keys = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 獲取過去一個月的日記資料，並回傳聚合後的圖表資料和 AI 分析摘要
@app.route("/api/monthly_dashboard", methods=["GET"])
def get_monthly_dashboard():
    print("[GET] Monthly Dashboard GET, received data:", request.form)
    
    # 從 DB 取出一個月內的日記（DiaryRecord 格式）
    start_date = str(datetime.now().date() - relativedelta(months=1))
    end_date = str(datetime.now().date())
    diary_records = DBdata_to_diary_records(db.date_period_select(start_date, end_date))
    
    # 直接聚合生成圖表
    dashboard_payload = aggregate_weekly_records(diary_records)
    ai_summary = summarize_health_trend(dashboard_payload).replace("\n", "<br>")  # 將換行轉成 HTML 的 <br>，方便前端顯示

    print("[GET] Monthly Dashboard Summary:")
    print(ai_summary)
    
    dashboard_payload["cooccurrence_chart"] = coocurrence_to_chart(dashboard_payload["cooccurrence_chart"]["pair_summary"])
    return jsonify({
        "weekly_dashboard": dashboard_payload,
        "groq_summary": ai_summary,
    })

# 將 coocurrence 的格式轉換成適合 chart.js 的格式
def coocurrence_to_chart(data):
    symptoms, positive_counts, negative_counts = [], [], []
    
    for i in data:
        if i["symptom"] not in symptoms:
            symptoms.append(i["symptom"])
            if i["emotion"] == "positive":
                positive_counts.append(i["count"])
                negative_counts.append(0)
            else:
                positive_counts.append(0)
                negative_counts.append(-1*i["count"])
        else:
            index = symptoms.index(i["symptom"])
            if i["emotion"] == "positive":
                positive_counts[index] = i["count"]
            else:
                negative_counts[index] = -1 * i["count"]
                
    return {
        "labels": symptoms,
        "positive_counts": positive_counts,
        "negative_counts": negative_counts
    }

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
            
            symptom["key"] = translate_to(symptom["key"], target)
            
            # 翻譯所有時間跟頻率，只保留翻譯結果
            for i in range(len(symptom['times'])):
                symptom['times'][i] = translate_to(symptom['times'][i], target)
                
            for i in range(len(symptom['frequencies'])):
                symptom['frequencies'][i] = translate_to(symptom['frequencies'][i], target)
        
        for medication in diary_record_view["medications"]: # 翻譯用藥
            # 如果沒有 key 就顯示 display，保留原文跟翻譯結果
            if not medication["key"]:
                medication["key"] = medication["display"]
            del medication["display"]
            
            # [0]: 原文, [1]: 翻譯結果
            medication["key"] = [medication["key"]]
            medication["key"].append(translate_to(medication["key"][0], target))
            
            # 翻譯所有時間跟頻率，只保留翻譯結果
            for i in range(len(medication['dosages'])):
                medication['dosages'][i] = translate_to(medication['dosages'][i], target)
                
            for i in range(len(medication['frequencies'])):
                medication['frequencies'][i] = translate_to(medication['frequencies'][i], target)
        
        # 存 diary data 到 DB
        db.diary_insert(text, diary_record_view)
        print("Diary Record View:", diary_record_view)    
        return jsonify(diary_record_view)

# 接收前端送來的醫囑內容，並回傳分析結果
@app.route("/medical_process", methods=["POST"])
def process_medical():
    if request.method == "POST":
        print("[POST] Medical Process POST, received data:", request.form)
        
        # 取出前端傳來的資料
        data = request.form
        text = data["message"]
        target_lang = data["language"]
        
        # 翻譯醫囑
        text_translated = translate_to(text, target_lang)
        
        # 偵測醫囑PHI
        phi, medicine = call_phi_service(text)
        print(phi)
        
        #給所有PHI翻譯，並把翻譯加入 phi(dict)
        for key in ["病名","症狀"]:
            value = phi[key]
            tmp = {"original": value, "translated": []}
            for i in value:
                tmp["translated"].append(translate_to(i, target_lang))
            phi[key] = tmp
        for medicine in phi["藥劑"]:
            for key, value in medicine.items():
                if key == "藥名":
                    medicine[key] = [value, translate_to(value, target_lang)]
                    _url = get_wiki_info(value)
                else:
                    tmp = {"original": value, "translated": []}
                    for i in value:
                        tmp["translated"].append(translate_to(i, target_lang))
                    medicine[key] = tmp
            medicine['url'] = _url
        
        # 回傳結果給前端
        result = {
            "date": str(datetime.now().date()),
            "text": text,
            "translated_text": text_translated,
            "target_language": target_lang,
            "phi": phi
        }
        db.medical_insert(result)
        print("Medical Result:", result)
        return jsonify(result)
 
# 執行語音錄入並回傳錄入文字   
@app.route("/speech_to_text", methods=["POST"])
def speech():
    print("[POST] Speech to Text POST")
    result = speech_to_text()
    return jsonify(result)

# 接收前端送來的內容，並回傳PII審核結果
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

# 取得歷史紀錄
@app.route("/history_get", methods=["POST"])
def db_select():
    print("[POST] History Get POST, received data:", request.form)
    
    # 取出前端傳來的資料
    text = request.form
    database = text["class"]

    # 搜尋對應 database 中的所有資料
    if database == "diary":
        result = db.diary_find()
    elif database == "medical":
        result = db.medical_find()
    else:
        return jsonify(None)
    
    # 按照日期降序排序，並轉成list以便處理
    result.sort("date",-1)
    result = list(result)
    return jsonify(result)

# 一打開網站要做的事情
@app.route("/")
def home():
    print("[GET] Home GET")
    return render_template("diary.html")

# 前往情緒日記頁面
@app.route("/diary")
def diary():
    return render_template("diary.html")

# 前往醫囑頁面
@app.route("/medical")
def medical():
    return render_template("medical.html")

# 前往圖表頁面
@app.route("/graph")
def graph():
    return render_template("graph.html")

# 將 DB 中取出的資料轉為 diary records
def DBdata_to_diary_records(DBdata):
    DBdata = list(DBdata)
    for d in DBdata:
        for symptom in d["symptoms"]:
            symptom["display"] = symptom["key"]
        for medication in d["medications"]:
            medication["key"] = medication["key"][1]
            medication["display"] = medication["key"]
    return DBdata

if __name__ == "__main__":
    db.connect()
    app.run()