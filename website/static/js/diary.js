var message_tmp = "";   // 暫存 PII 遮蔽過後的結果

$(function(){
    // 左欄按鈕(輸入狀態)
    $("#analyze").click(pii_check);
    $("#erase").click(function() {
        $("#message").val("");
    });

    // PII浮窗按鈕
    $("#pii-redacted").click(() => diaryProcess(message_tmp));  // 遮蔽PII後再分析
    $("#ignore").click(() => diaryProcess(null));   // 直接分析
});

// PII檢測
function pii_check() {
    let message = $("#message").val();

    //先確認日記內容裡是否有PII
    $.post("/pii_review", {text: message}, function (data) {
        if(data.needs_masking == true) {    //偵測到 PII
            // 顯示浮窗
            const overlay = $("#overlay");
            overlay.show();
            message_tmp = "";

            // 在浮窗中將PII醒目標示
            const popupText = $("#popup_text");
            let popupHtml = ``;
            let p = 0;
            for(const entity of data.entities) {
                popupHtml += message.slice(p, entity.start);
                message_tmp += message.slice(p, entity.start);

                popupHtml += `<span class="pii-entity">${message.slice(entity.start, entity.end)}</span>`;
                message_tmp += "▉".repeat(entity.end - entity.start);

                p = entity.end;
            }
            if(p < message.length){
                popupHtml += message.slice(p);
                message_tmp += message.slice(p);
            }
            popupText.html(popupHtml);
        }
        else    //沒有偵測到PII，直接開始分析
            diaryProcess(null);
    });
}

// 執行日記分析
function diaryProcess(message) {
    // 隱藏PII浮窗
    const overlay = $("#overlay");
    overlay.hide();

    // 取得輸入資料
    let date = $("#date").val();
    if(!message)
        message = $("#message").val();

    let params = {
        date: date,
        message: message
    };

    // 發送分析請求並顯示結果
    $.post("/diary_process", params, function (data) {
        
    });
}

// 顯示日記分析結果
function resultShow(data) {
    const resultCol = $("#result-col");
    let htmlContent = `<div class="float-row">`;
    if (data.emotion_label == 'neutral')
    

    resultCol.append(htmlContent);
}