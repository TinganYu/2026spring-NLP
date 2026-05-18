import sys
import os

# 將 2026-NLP路徑 設為import時搜尋的第一順位
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)   # 2026-NLP路徑
sys.path.insert(0,parent_dir)

import configparser
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from dataclasses import asdict
from flask import Flask, request, abort, render_template, url_for, Blueprint, jsonify
from diary.processor import process_entry
from shared.pii import review_pii
import website.database as db
from diary.aggregator import aggregate_weekly_records
from diary.models import AnalysisResult, DiaryEntry, EmotionResult 

# Config Parser
config = configparser.ConfigParser()
config.read("config.ini")

UPLOAD_FOLDER = "website"

app = Flask(__name__)
app.json.sort_keys = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def _remove_data_sources(obj): # 因為PHI提供的data sources 實在是太多了，看得有點花。回傳時就先不加入這個欄位，但是看DB要不要存囉
    """遞迴移除所有巢狀結構中的 data_sources 欄位，但保留其他資料。"""
    if isinstance(obj, dict):
        return {k: _remove_data_sources(v) for k, v in obj.items() if k != "data_sources"}
    elif isinstance(obj, list):
        return [_remove_data_sources(item) for item in obj]
    else:
        return obj

# @app.route("/api/entity-mapping/<entity_id>", methods=["GET"]) # 之後如果有做需要entity標籤的東西才會需要，請無視
# def get_entity_mapping(entity_id):
#     # 從數據庫取得完整的entity數據(尤其是data sources)
#     # 之後建好再加入程式
#     pass

@app.route("/api/weekly_dashboard", methods=["GET"])
def get_weekly_dashboard():
    user_id = request.args.get("user_id") # 或是從 session 拿
    # 這裡可以讓前端傳日期，或是後端自動推算過去 7 天
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date")
    
    # 1. 從 MongoDB 撈出這段時間的日記 (這部分要看你們 db.py 的實作)
    # 假設 db.get_diaries_by_range 回傳的是一個 dict 列表
    raw_db_records = db.get_diaries_by_range(user_id, start_date, end_date)
    
    # 2. 將 DB 資料還原成 aggregator 認得的 AnalysisResult 物件列表
    analysis_records = []
    for doc in raw_db_records:
        # 從你當初存進 Mongo 的結構中把資料拿出來組裝 (這段是AI亂寫的，反正之後看DB怎麼存再改)
        entry = DiaryEntry(text=doc["text"], meta={"date": doc["date"]})
        emotion = EmotionResult(label=doc["emotion_label"], score=doc["emotion_score"])
        # 原始的 phi 結構存在 doc["raw_analysis"]["phi"]
        phi_data = doc.get("raw_analysis", {}).get("phi", {})
        # 組裝成 AnalysisResult
        record = AnalysisResult(
            entry=entry,
            emotion=emotion,
            symptoms=[], # 轉成 DiaryRecord 時主要是看 extra["phi"]，這裡維持空 list 即可
            extra={"phi": phi_data}
        )
        analysis_records.append(record)
        
    # 3. 呼叫聚合器，直接生成所有圖表
    dashboard_payload = aggregate_weekly_records(analysis_records)
    
    # 4. 回傳給前端，前端接去畫圖即可
    return jsonify(dashboard_payload)

@app.route("/diary_process", methods=["POST"])  #接收前端送來的日記內容，並回傳分析結果
def process_diary():
    if request.method == "POST":
        print("POST!")
        text = request.json.get("text") #日記內容 (理想是先呼叫PII，使用者決定是否要遮蔽，然後再送原始訊息或是處理後的訊息到這裡分析)
        meta = request.json.get("meta") #使用者資訊(可能之後看情況會刪?)
        result = process_entry(text, meta)
        result_dict = asdict(result)
        # 移除 API 回傳中的 data_sources（保留完整內部數據）
        cleaned_result = _remove_data_sources(result_dict)
        return jsonify(cleaned_result)

@app.route("/diary_pii_review", methods=["POST"])  #接收前端送來的內容，並回傳PII審核結果
def diary_pii_review():
    text = request.json.get("text", "")
    review = review_pii(text)
    return jsonify(asdict(review))

@app.route("/")  #一打開網站要做的事情
def home():
    db.connect()
    return render_template("diary.html")

if __name__ == "__main__":
    app.run()