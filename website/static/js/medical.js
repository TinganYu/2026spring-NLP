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
    // 隱藏非選取的語言按鈕
    $(".language-btn").hide();
    const languageShow = $(`#${data.target_language}`), languageNow = $(".language-btn.select");
    if (languageNow.attr("id") != languageShow.attr("id")){
        languageShow.addClass("select");
        languageNow.removeClass("select");
    }
    languageShow.show();

    const resultCol = $("#result-col");
    resultCol.children().not("#language-row").remove();
    containerHtml = `<div class="float-row"></div>`;

    // 產生病名+症狀的表格內容
    const tableContainer = $(containerHtml);
    let tableHtml = `
    <h3>病名＆症狀</h3>
    <table>
        <tr>
            <th>標籤</th>
            <th>原文</th>
            <th>翻譯結果（${$(".language-btn.select").text()}）</th>
        </tr>`;
    let showBool = false;

    for (const key of ["病名", "症狀"]) {
        const value = data.phi[key];
        for (let i = 0; i < value.original.length; i++) {
            if(!showBool)
                showBool = true;
            
            tableHtml += `
            <tr>
                <td><span class="${key} table-tag">${key}</span></td>
                <td>${value.original[i]}</td>
                <td>${value.translated[i]}</td>
            </tr>
            `;
        }
    }
    tableHtml += `</table>`;
    tableContainer.html(tableHtml);

    if(showBool)
        resultCol.append(tableContainer);

    // 產生各個藥劑的表格內容
    for(const medicine of data.phi.藥劑){
        const medicineContainer = $(containerHtml);
        showBool = false;
        let medicineHtml = `
            <div class="row">
                <h3>${medicine.藥名[1]}（${medicine.藥名[0]}）</h3>
                <a href="${medicine.url}" target="_blank">
                    <button class="img-btn">
                        <img src="/static/image/link-icon.png" style="height:30px; width:30px;">
                    </button>
                </a>
            </div>
            <table>
                <tr>
                    <th>標籤</th>
                    <th>原文</th>
                    <th>翻譯結果（${$(".language-btn.select").text()}）</th>
                </tr>`;
        
        for(const key of ["劑量", "頻率", "註記"]){
            if(medicine[key].original.length > 0){
                if(!showBool)
                    showBool = true;
                const originAll = medicine[key].original.join(", ");
                const transAll = medicine[key].translated.join(", ");
                medicineHtml +=  `
                <tr>
                    <td><span class="${key} table-tag">${key}</span></td>
                    <td>${originAll}</td>
                    <td>${transAll}</td>
                </tr>
                `;
            }
        }

        medicineHtml += `</table>`;
        medicineContainer.html(medicineHtml);
        resultCol.append(medicineContainer);
        if(!showBool)
            medicineContainer.find("table").remove();
    }

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