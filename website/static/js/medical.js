var message_tmp = "";

$(function(){
    $("#analyze").click(pii_check);
    $("#erase").click(function() {
        $("#message").val("");
    });
    $("#pii-redacted").click(() => medicalProcess(message_tmp));
    $("#ignore").click(() => medicalProcess(null));

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
    var message = $("#message").val();

    //先確認醫囑內容裡是否有PII
    $.post("/pii_review", {text: message}, function (data) {
        if(data.needs_masking == true) {
            const overlay = $("#overlay");
            overlay.show();//overlay.style.display = "block";
            //message_tmp = data.redacted_text;
            message_tmp = "";

            // 在浮窗中將PII醒目標示
            const popupText = $("#popup_text");
            var popupHtml = ``;
            var p = 0;
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
            console.log(message_tmp);
            popupText.html(popupHtml);//popupText.innerHTML = popupHtml;
        }
        else
            medicalProcess(null);
    });
}

function medicalProcess(message) {
    const overlay = $("#overlay");
    overlay.hide();//overlay.style.display = "none";

    if(!message)
        message = $("#message").val();

    var params = {
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

    var tableHtml = `
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
}