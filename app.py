import sys
import configparser
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from dataclasses import dataclass, asdict
from flask import Flask, request, abort, render_template, url_for, Blueprint, jsonify
from diary.processor import process_entry

# Config Parser
config = configparser.ConfigParser()
config.read("config.ini")

UPLOAD_FOLDER = "website"

app = Flask(__name__)
app.json.sort_keys = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def _remove_data_sources(obj): # 因為data sources 實在是太多了，看得有點花。回傳時就先不加入這個欄位，但是提供router之後可以取得完整資料
    """遞迴移除所有巢狀結構中的 data_sources 欄位，但保留其他資料。"""
    if isinstance(obj, dict):
        return {k: _remove_data_sources(v) for k, v in obj.items() if k != "data_sources"}
    elif isinstance(obj, list):
        return [_remove_data_sources(item) for item in obj]
    else:
        return obj

@app.route("/api/entity-mapping/<entity_id>", methods=["GET"])
def get_entity_mapping(entity_id):
    # 從數據庫取得完整的entity數據(尤其是data sources)
    # 之後建好再加入程式
    pass

@app.route("/diary_process", methods=["POST"])
def process_diary():
    if request.method == "POST":
        print("POST!")
        text = request.json.get("text")
        meta = request.json.get("meta")
        result = process_entry(text, meta)
        result_dict = asdict(result)
        # 移除 API 回傳中的 data_sources（保留完整內部數據）
        cleaned_result = _remove_data_sources(result_dict)
        return jsonify(cleaned_result)


@app.route("/")  #一打開網站要做的事情
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()