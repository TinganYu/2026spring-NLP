import sys
import os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# 將 2026-NLP路徑 設為import時搜尋的第一順位
import configparser
from flask import Flask, request, abort, render_template, url_for, Blueprint, jsonify
from diary.processor import process_entry
from shared.pii import review_pii
import website.database as db
from diary.analysis import to_diary_record
from diary.aggregator import aggregate_weekly_records 
from dataclasses import asdict

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
    user_id = request.args.get("user_id")
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date")
    
    # 從 DB 取出時間範圍內的日記（AnalysisResult 格式）
    analysis_records = db.get_diaries_by_range(user_id, start_date, end_date)
    
    # 直接聚合生成圖表
    dashboard_payload = aggregate_weekly_records(analysis_records)
    return jsonify(dashboard_payload)

@app.route("/diary_process", methods=["POST"])  #接收前端送來的日記內容，並回傳分析結果
def process_diary():
    if request.method == "POST":
        print("POST!")
        text = request.json.get("text")
        meta = request.json.get("meta")
        result = process_entry(text, meta)  # AnalysisResult dict
        cleaned_result = _remove_data_sources(result)  # 移除 data sources
        if hasattr(db, "save"):
            db.save(cleaned_result)  # 存整個 AnalysisResult 到 DB
        
        # 同時轉成 DiaryRecord 回傳給前端
        diary_record_view = to_diary_record(result, (meta or {}).get("date", ""))
        return jsonify({
            "raw_saved": cleaned_result,
            "view_model": diary_record_view 
        })

@app.route("/diary_pii_review", methods=["POST"])  #接收前端送來的內容，並回傳PII審核結果
def diary_pii_review():
    text = request.json.get("text", "")
    review = review_pii(text) 
    return jsonify(review)

@app.route("/")  #一打開網站要做的事情
def home():
    db.connect()
    return render_template("diary.html")

if __name__ == "__main__":
    app.run()