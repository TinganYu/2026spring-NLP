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
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/diary_process", methods=["POST"])
def process_diary():
    if request.method == "POST":
        print("POST!")
        text = request.json.get("text")
        meta = request.json.get("meta")
        result = process_entry(text, meta)
        return jsonify(asdict(result))  # 因為flask只能處理可序列化的資料，所以把 dataclass 轉成 jasonify 再回傳


@app.route("/")  #一打開網站要做的事情
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()