var message_tmp = "";
$(function(){
    $("#analyze").click(pii_check);
    $("#erase").click(function() {
        $("#message").val("");
    });
    $("#pii-redacted").click(() => diaryProcess(message_tmp));
    $("#ignore").click(() => diaryProcess(null));
});

function pii_check() {
    var date = $("#date").val();
    var message = $("#message").val();

    //先確認日記內容裡是否有PII
    $.post("/pii_review", {text: message}, function (data) {
        // PII Review Result: {'needs_masking': True, 
        // 'entities': [{'text': '陳芊羽', 'category': 'Person', 'start': 2, 'end': 5, 'confidence_score': 1.0}], 
        // 'redacted_text': '我是[PERSON-1] 測試'}
        if(data.needs_masking == true) {
            const overlay = document.getElementById("overlay");
            overlay.style.display = "block";
            message_tmp = data.redacted_text;

            // 在浮窗中將PII醒目標示
            const popupText = document.getElementById("popup_text");
            var popupHtml = ``;
            var p = 0;
            for(const entity of data.entities) {
                popupHtml += message.slice(p, entity.start);
                popupHtml += `<span class="pii-entity">${message.slice(entity.start, entity.end)}</span>`;
                p = entity.end;
            }
            if(p < message.length)
                popupHtml += message.slice(p);
            popupText.innerHTML = popupHtml;
        }
        else
            diaryProcess(null);
    });
}

function diaryProcess(message) {
    const overlay = document.getElementById("overlay");
    overlay.style.display = "none";

    var date = $("#date").val();
    if(!message)
        message = $("#message").val();

    var params = {
        date: date,
        message: message
    };

    $.post("/diary_process", params, function (data) {
        //結果呈現等確定要怎麼做
        /*const resultDiv = document.getElementById("result-col");
        var htmlContent = `<div class="float-row" style="border-left: 4px solid orange;">`;
        if (data.emotion_label == 'neutral')
        

        resultDiv.insertAdjacentHTML('beforeend', `
            <div class="float-row" style="border-left: 4px solid orange;">
                <span></span>
            </div>
        `);*/
    });
}

function erase_textarea() {
    $("#message").val("");
}