let message_tmp = "";

$(function(){
    $("#analyze").click(pii_check);
    $("#erase").click(function() {
        $("#message").val("");
    });
    $("#pii-redacted").click(() => medicalProcess(message_tmp));
    $("#ignore").click(() => medicalProcess(null));
    $("#return").click(function() {
        window.location.replace("/medical");
    });
    $("#upload-mp3").click(speechToText);

    const langs = $(".language-btn");
    langs.click(function() {
        const nowLang = $(".language-btn.select");
        if(nowLang.attr("id") != $(this).attr("id")){
            nowLang.removeClass("select");
            $(this).addClass("select");
        }
    });
});

function pii_check() {
    let message = $("#message").val();

    //先確認醫囑內容裡是否有PII
    $.post("/pii_review", {text: message}, function (data) {
        if(data.needs_masking == true) {
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
            if(p < message.length) {
                popupHtml += message.slice(p);
                message_tmp += message.slice(p);
            }
            popupText.html(popupHtml);
        }
        else
            medicalProcess(null);
    });
}

function medicalProcess(message) {
    const overlay = $("#overlay");
    overlay.hide();

    if(!message)
        message = $("#message").val();

    let params = {
        language: $(".language-btn.select").attr("id"),
        message: message
    };

    $.post("/medical_process", params, function (data) {
        resultShow(data);
    });
}

function resultShow(data){
    // 顯示表格
    const tableContainer = $("#table-container");
    tableContainer.show();
    $(".language-btn").hide();
    $(".language-btn.select").show();

    let tableHtml = `
    <table>
        <tr>
            <th>標籤</th>
            <th>醫療實體內容(原文)</th>
            <th>目標語言翻譯結果(${$(".language-btn.select").text()})</th>
        </tr>`;

    for (const [key, value] of Object.entries(data.phi)) {
        console.log(key, value);
        console.log(value.original.length);
        console.log(value.original);
        for (let i = 0; i < value.original.length; i++) {
            // 之後再補上欄位樣式
            tableHtml += `
            <tr>
                <td>${key}</td>
                <td>${value.original[i]}</td>
                <td>${value.translated[i]}</td>
            </tr>
            `;
        }
    }
    tableHtml += `</table>`;
    tableContainer.html(tableHtml);

    // 顯示原文跟翻譯後結果
    $("#input-col").hide();
    $("#output-col").show();
    $("#original-text").val(data.original_text);
    $("#translated-text").val(data.translated_text);
}

function speechToText() {
    $("#speech-overlay").show();
    $.post("/speech_to_text", {}, function (data) {
        $("#speech-overlay").hide();
        $("#message").val(data);
    });
}