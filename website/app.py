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

# Config Parser
config = configparser.ConfigParser()
config.read("config.ini")

UPLOAD_FOLDER = "website"

app = Flask(__name__)
app.json.sort_keys = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def _remove_data_sources(obj): # 因為PHI提供的data sources 實在是太多了，看得有點花。回傳時就先不加入這個欄位，但是提供router之後可以取得完整資料
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
    return render_template("index.html")

if __name__ == "__main__":
    app.run()