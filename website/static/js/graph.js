let chartArr = [null, null, null, null];    //暫存圖表們以便清除

$(function(){
    // 從後端獲取所有所需資料並嵌入頁面
    $.get("/api/monthly_dashboard", function(data){
        $("#ai-summary-content").html(data.groq_summary);
        MainDataShow(data.weekly_dashboard);
        addChart(data);
    });
});

// 重點資訊嵌入
function MainDataShow(data){
    // 資料時間範圍
    let tmp = $("#time-range");
    tmp.find("p, span").remove();
    tmp.append(`<p style="display: inline-block;">${data.week_start}</p><span> ~</span>
                <p style="margin-top: 0;">${data.week_end}</p>
                <span>(共${data.record_count}筆)</span>`);
    
    // 情緒統計
    let _data = data.emotion_statistics;
    let _text = {"positive": "正向為主", "negative": "負向為主", "neutral": "情緒穩定"};
    tmp = $("#most-emotion");
    tmp.find("p, span, img").remove();
    tmp.append(`<div class="row">
                    <img src="/static/image/${_data.most_common_label}-icon.png" style="width:100px; height:100px; margin: 10px;">
                    <p style="display: inline-block; margin: auto 0;">${_text[_data.most_common_label]}</p>
                </div>
                <div class="row" style="margin-top: 20px; gap:10px;">
                    <span class="table-tag 藥名">正向 ${_data.label_distribution.positive} 天</span>
                    <span class="table-tag 症狀">負向 ${_data.label_distribution.negative} 天</span>
                    <span class="table-tag 註記">情緒強度：${_data.average_score}</span>
                </div>`);
    
    // 趨勢分析
    _text = {"improving": "好轉中", "declining": "惡化中", "stable": "持續穩定"};
    tmp = $("#trend");
    tmp.find("p, span").remove();
    tmp.append(`<p> ${_text[_data.trend_direction]} </p>`);

    // 最常出現症狀
    _data = data.symptom_frequency_chart.labels;
    let _data2 = data.symptom_frequency_chart.series[0].data;
    tmp = $("#most-symptom");
    tmp.find("p, span").remove();
    tmp.append(`<p style="margin-bottom:10px;"> ${_data[0]} </p>
                <span>累積出現 ${_data2[0]} 次</span>`);

    if(_data2[1] == _data2[0]){ // 如果出現次數有相同，都列出來
        let i=2;
        let str_tmp = `<br>相同次數的症狀：${_data[1]}`;
        while(_data2[i] == _data2[0]){
            str_tmp += `, ${_data[i]}`;
            i++;
        }
        tmp.append(`<span>${str_tmp}</span>`);
    }
}

// 將圖表嵌入頁面
function addChart(data) {
    for (const chartId of ["emotion_line_chart", "symptom_frequency_chart", "medication_frequency_chart", "cooccurrence_chart"]) {
        const canvas = $(`#${chartId}`)[0];
        const _data = data.weekly_dashboard[chartId];

        if (chartId == "emotion_line_chart")    // 時間v.s.情緒指數 折線圖
            addLineChart(canvas, _data.labels, _data.series[0].data);

        else if (chartId == "symptom_frequency_chart"){ // 症狀次數 柱狀圖
            if(chartArr[1]) 
                chartArr[1].destroy();
            chartArr[1] = addBarChart(canvas, _data.labels, _data.series[0].data, '症狀');
        }

        else if (chartId == "medication_frequency_chart"){  // 用藥次數 柱狀圖
            if(chartArr[2]) 
                chartArr[2].destroy();
            chartArr[2] = addBarChart(canvas, _data.labels, _data.series[0].data, '用藥');
        }

        else {  // 情緒v.s.症狀 正負柱狀圖
            if(chartArr[3]) 
                chartArr[3].destroy();
            chartArr[3] = addStackedBarChart(canvas, _data.labels, _data.positive_counts, _data.negative_counts);
        }
    }
}

// 生成折線圖
function addLineChart(canvas, labels, datas){
    if(chartArr[0]) 
        chartArr[0].destroy();

    chartArr[0] = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '情緒指數',
                    data: datas,
                    fill: false,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    tension: 0.3
                }]
            },
            options: options("日期",null,false)
        });
}

// 生成柱狀圖
function addBarChart(canvas, labels, datas, label_name){
    return new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label_name+"次數",
                    data: datas,
                    backgroundColor: 'rgb(83, 214, 188)',
                    borderColor: 'rgb(58, 151, 129)',
                    borderWidth: 1
                }]
            },
            options: options(null,null,true)
        });
}

// 生成堆疊柱狀圖
function addStackedBarChart(canvas, labels, data_positive, data_negative){
    _options = options(null,null,true);
    _options.scales.x.stacked = true;
    _options.scales.y.stacked = true;

    return new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: "正向情緒",
                    data: data_positive,
                    backgroundColor: 'rgb(94, 211, 143)',
                    borderColor: 'rgb(39, 174, 96)',
                    borderWidth: 1,
                    stack: 'Stack 0'  
                },{
                    label: "負向情緒",
                    data: data_negative,
                    backgroundColor: 'rgb(245, 135, 123)', 
                    borderColor: 'rgb(192, 57, 43)',
                    borderWidth: 1,
                    stack: 'Stack 0' 
                }]
            },
            options: _options
        });
}

// 回傳所有圖表共用的設定選項
function options(x_text, y_text, legend_display){
    result = {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: x_text
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: y_text
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: legend_display
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            };
    
    // 如果沒傳入x軸或y軸標題文字，則不顯示標題
    if(!x_text)
        result.scales.x.title.display = false;
    if(!y_text)
        result.scales.y.title.display = false;
    
    return result;
}