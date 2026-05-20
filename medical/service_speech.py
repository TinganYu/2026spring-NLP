'''
使用Azure 語音辨識服務，將使用者的語音轉換為文字
配合醫療場景中自然的停頓和換氣，確保使用者講完一段話後才會結束辨識

輸入: 無（直接從麥克風錄音)
輸出: 辨識後的文字結果
'''

import azure.cognitiveservices.speech as speechsdk
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

def speech_to_text() -> str:
    """錄製一段完整的話：允許說話中間有自然停頓，直到整段話結束後自動中斷"""
    speech_config = speechsdk.SpeechConfig(
        subscription=config["AzureSpeech"]["KEY"],
        region=config["AzureSpeech"]["REGION"]
    )
    speech_config.speech_recognition_language = "zh-TW" 
    
    # 核心關鍵：調整 Azure 對「完整一句話結束」的静音判定標準
    # 預設通常只有 500~1000 毫秒，這會導致換氣就中斷。
    # 我們將其提高到 8000 毫秒 (8 秒)。
    # 這樣中間正常的換氣、看病歷的短暫停頓都不會中斷，直到你整段講完並安靜 8 秒才會觸發結束。
    speech_config.set_property(
        speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, 
        "8000"
    )
    
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    print(" 麥克風已啟動，請開始說話...")
    
    # 使用單次非同步辨識，配合調高後的結束判定，最適合「講完一段話就收工」的場景
    result = speech_recognizer.recognize_once_async().get()
    
    # 判定結果
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "無法辨識語音，請確認麥克風是否正常，或嘗試重新說話。"
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        return f"語音辨識取消，原因: {cancellation_details.reason}。錯誤訊息: {cancellation_details.error_details}"
    
    return ""

if __name__ == "__main__":
    text_result = speech_to_text()
    print("\n==================== 最終辨識結果 ====================")
    print(text_result)
    print("======================================================")