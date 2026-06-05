var message_tmp = "";   // 暫存 PII 遮蔽過後的結果

// 執行日記分析
function dataProcess(message) {
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
        resultShow(data);
    });
}

// 顯示日記分析結果
function resultShow(data) {
    resultClean();   // 清除舊結果
    const resultCol = $("#result-col");
    $("#message").val(data.text);

    // 新增 今日情緒 結果顯示行
    let htmlContent = `
    <div class="float-row result-row">
        <h3>今日情緒</h3>
        <div style="grid-column: 1; padding: 10px; display:flex;">`;

    // 根據情緒加入圖標與文字
    htmlContent += `<img src="/static/image/${data.emotion_label}-icon.png" style="width:10vh; height:10vh; margin-right:15px;">`;
    if (data.emotion_label == 'negative')
        htmlContent += `<span class="emotion-label">負面情緒</span>`;
    else if (data.emotion_label == 'positive')
        htmlContent += `<span class="emotion-label">正面情緒</span>`;
    else if (data.emotion_label == 'neutral')
        htmlContent += `<span class="emotion-label">中性情緒</span>`;
    
    // 顯示情緒強度
    let emotion_score = data.emotion_score.toFixed(2) * 100;
    htmlContent += `</div>
        <div style="grid-column: 2; justify-content: flex-end; display:flex;">
            <div class="column" style="align-items: center; margin-right: 40px;">
                <div class="score-bar">
                    <div class="score-bar ${data.emotion_label}" style="width: ${emotion_score}%;"></div>
                </div>
                <p>情緒強度 ${emotion_score}%</p>
            </div>
        </div>
    </div>`;
    resultCol.append(htmlContent);

    // 新增 症狀紀錄 結果顯示行
    if (data.symptoms.length > 0) { //因為要給button綁事件所以這裡程式要改漂亮點
        htmlContent = `
        <div class="float-row" id="symptom">
            <h3>症狀紀錄</h3>`;

        // 以每個症狀為一行顯示
        for (const symptom of data.symptoms) {
            htmlContent += `<div class="row inblock-row">`;

            // 顯示疼痛程度
            if (symptom.status != "affirmed")
                htmlContent += `
                <div class="dot"></div>
                <div class="column">
                    <div class="row" style="gap:5px;">
                    <span style="font-weight: bold;">${symptom.key}</span>`;
            else if (symptom.severity == 2)
                htmlContent += `
                <div class="dot pan-mid"></div>
                <div class="column">
                    <div class="row" style="gap:5px;">
                    <span style="font-weight: bold;">${symptom.key}</span>
                    <button class="label label-2">中等</button>`; //<span class="material-symbols-outlined">edit</span>
            else if (symptom.severity == 1)
                htmlContent += `
                <div class="dot neutral"></div>
                <div class="column">
                    <div class="row" style="gap:5px;">
                    <span style="font-weight: bold;">${symptom.key}</span>
                    <button class="label label-1">輕度</button>`;
            else
                htmlContent += `
                <div class="dot negative"></div>
                <div class="column">
                    <div class="row" style="gap:10px;">
                    <span style="font-weight: bold;">${symptom.key}</span>
                    <button class="label label-3">嚴重</button>`;

            // 顯示症狀狀態
            if (symptom.status == "affirmed")
                htmlContent += `<span class="label">正在發生</span><br>`;
            else if (symptom.status == "hypothetical")
                htmlContent += `<span class="label">可能發生</span><br>`;
            else if (symptom.status == "historical")
                htmlContent += `<span class="label">已消失</span>`;
            htmlContent += `</div>`;

            // 顯示發生時間與發生頻率
            if (symptom.times.length > 0){
                htmlContent += `<img><p>發生時間：${symptom.times[0]}`;
                for (let i = 1; i < symptom.times.length; i++)
                    htmlContent += `,${symptom.times[i]}`;
                htmlContent += `</p>`;
            }

            if (symptom.frequencies.length > 0){
                htmlContent += `<img><p>發生頻率：${symptom.frequencies[0]}`;
                for (let i = 1; i < symptom.frequencies.length; i++)
                    htmlContent += `,${symptom.frequencies[i]}`;
                htmlContent += `</p>`;
            }

            htmlContent += `</div></div>`;
        }
        htmlContent += `</div>`;
    }

    // 新增 用藥紀錄 結果顯示行
    if (data.medications.length > 0) {
        htmlContent += `
        <div class="float-row medication" style="display: flex; flex-direction: column;">
            <h3>用藥紀錄</h3>`;

            // 以每個用藥為一行顯示
            for (const medication of data.medications){
                htmlContent += `<div class="inblock-row result-row">
                    <div class="row" style="grid-column: 1;">
                        <img src="/static/image/medication.png" style="width:50px; height:50px; margin-right:15px; border-radius: 15px;">
                        <div class="column">
                            <p style="font-weight: bold;">${medication.key[1]}</p>
                            <p>${medication.key[0]}</p>
                        </div>
                    </div>
                    <div style="grid-column: 2; justify-content: flex-end; display:flex;">
                        <div class="column" style="margin-right: 15px;">`;
                
                // 顯示用藥頻率與用量
                if (medication.frequencies.length > 0){
                    htmlContent += `<p>${medication.frequencies[0]}`;
                    for (let i = 1; i < medication.frequencies.length; i++)
                        htmlContent += `,${medication.frequencies[i]}`;
                    htmlContent += `</p>`;
                }

                if (medication.dosages.length > 0){
                    htmlContent += `<p style="color: #7f7f7f; font-size: 14px;">${medication.dosages[0]}`;
                    for (let i = 1; i < medication.dosages.length; i++)
                        htmlContent += `,${medication.dosages[i]}`;
                    htmlContent += `</p>`;
                }

                htmlContent += `</div></div></div>`;
            }
        htmlContent += `</div>`;
    }

    // 將html注入
    resultCol.append(htmlContent);
}

// 清空右欄結果顯示
function resultClean() {
    const resultCol = $("#result-col");
    resultCol.html(`
        <div class="float-row">
            <h2 style="display: inline;">當日情緒語意分析</h2>
            <button class="btn" id="history-btn">歷史紀錄</button>
        </div>`);
    $("#history-btn").click(historyShow);
}