$(function(){
    // 輸入欄(共通部分)
    $("#analyze").click(pii_check);
    $("#erase").click(function() {
        $("#message").val("");
    });

    // tab切換
    $("#medical-btn").click(() => switchTab("medical"));
    $("#diary-btn").click(() => switchTab("diary"));
    $("#graph-btn").click(() => switchTab("graph"));

    // 歷史紀錄
    $("#history-btn").click(historyShow);
    $("#history-close").click(historyHide);

    // PII浮窗按鈕
    $("#pii-redacted").click(function() {   // 遮蔽PII後再分析，並在左欄顯示分析結果
        $("#message").val(message_tmp);
        dataProcess(message_tmp);
    });

    $("#ignore").click(() => dataProcess(null));   // 直接分析
});

// 切換至點選tab
function switchTab(tab_name) {
    const nowTab = $(".tab.select");
    if (nowTab.attr("id") == tab_name+'-btn')   // 如果現在就在這個tab，不需要切換
        return;
    else
        window.location.replace("/"+tab_name);
}

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
            dataProcess(null);
    });
}

// 顯示歷史紀錄右欄，並加入每個紀錄的按鈕
function historyShow(){ //diary考慮到疼痛指數修改，也許data要留id
    // 顯示右欄並清除之前的紀錄按鈕
    $("#history-overlay").show();
    $(".history-block").remove();

    // 從後端取得歷史紀錄
    message = {class: $(".tab.select").attr("id").slice(0, -4)};
    $.post("/history_get", message , function (data) {
        let history_col = $("#history-col");

        // 以history-block的按鈕顯示每個歷史紀錄
        for (const d of data){
            const button = $(`<button class="history-block"></button>`);
            button.html(`
                <p>${d.date}</p>
                <p class="history-text">${d.text}</p>`);
            
            //按鈕綁定歷史紀錄的顯示
            button.click(function() { 
                historyHide();
                resultShow(d);
            });

            history_col.append(button);
        }
    });
}

// 將歷史紀錄側欄隱藏
function historyHide(){
    $("#history-overlay").hide();
}