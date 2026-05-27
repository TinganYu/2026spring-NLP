let message_tmp = "";   // 暫存 PII 遮蔽過後的結果

$(function(){
    // 左欄按鈕(輸入狀態)
    $("#upload-mp3").click(speechToText);

    // 左欄按鈕(輸出狀態)
    $("#return").click(function() {
        window.location.replace("/medical");
    });

    // 語言切換按鈕
    const langs = $(".language-btn");
    langs.click(function() {    // 當按鈕被點擊時，更新按鈕們的選取狀態 (class: select = 被選取)
        const nowLang = $(".language-btn.select");
        if(nowLang.attr("id") != $(this).attr("id")){
            nowLang.removeClass("select");
            $(this).addClass("select");
        }
    });
});

// 執行醫囑分析
function dataProcess(message) {
    // 隱藏PII浮窗
    const overlay = $("#overlay");
    overlay.hide();

    // 取得輸入資料
    if(!message)
        message = $("#message").val();

    let params = {
        language: $(".language-btn.select").attr("id"),
        message: message
    };

    // 發送分析請求並顯示結果
    $.post("/medical_process", params, function (data) {
        resultShow(data);
    });
}

// 醫囑分析結果顯示
function resultShow(data){
    // 顯示表格並隱藏非選取的語言按鈕
    const tableContainer = $("#table-container");
    tableContainer.show();
    $(".language-btn").hide();
    const languageShow = $(`#${data.target_language}`), languageNow = $(".language-btn.select");
    if (languageNow.attr("id") != languageShow.attr("id")){
        languageShow.addClass("select");
        languageNow.removeClass("select");
    }
    languageShow.show();

    // 產生表格內容
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

    // 左欄：顯示原文跟翻譯後結果
    $("#input-col").hide();
    $("#output-col").show();
    $("#original-text").val(data.text);
    $("#translated-text").val(data.translated_text);
}

// 語音輸入
function speechToText() {
    $("#speech-overlay").show();    // 顯示語音輸入中的浮窗
    $.post("/speech_to_text", {}, function (data) { // 執行語音輸入，並將輸入結果放進輸入框
        $("#speech-overlay").hide();
        $("#message").val(data);
    });
}