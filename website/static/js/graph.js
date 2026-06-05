let chartArr = [null, null, null, null];

$(function(){
    $.get("/api/weekly_dashboard", function(data){
        $("#ai-summary").append(`<p>${data.ai_summary}</p>`);
        MainDataShow(data);
        addChart(data);
    });
});

function MainDataShow(data){
    let tmp = $("#time-range");
    tmp.find("p, span").remove();
    tmp.append(`<p>${data.week_start}</p><span> ~</span>
                            <p>${data.week_end}</p>
                            <span>(共${data.record_count})</span>`);
    
    let _data = data.emotion_statistics;
    let _text = {"positive": "正向為主", "negative": "負向為主", "neutral": "情緒穩定"};
    tmp = $("#most-emotion");
    tmp.find("p, span, img").remove();
    tmp.append(`<img src="/static/image/${_data.most_common_label}-icon.png" style="width:100px; height:100px;">
                <p>${emotion_text[_data.most_common_label]}</p>
                <span class="table-tag 藥名">正向 ${_data.label_distribution.positive} 天</span>
                <span class="table-tag 症狀">負向 ${_data.label_distribution.negative} 天</span>
                <span class="table-tag 註記">情緒強度：${_data.average_score}</span>`);
    
    _text = {"improving": "好轉中", "declining": "惡化中", "stable": "持續穩定"};
    tmp = $("#trend");
    tmp.find("p, span").remove();
    tmp.append(``)
}

function addChart(data) {
    for (const chartId of ["emotion_line_chart", "symptom_frequency_chart", "medication_frequency_chart", "cooccurrence_chart"]) {
        const canvas = $(`#${chartId}`)[0];
        const _data = data.weekly_dashboard[chartId];
        // Initialize your charts here
        if (chartId == "emotion_line_chart") 
            addLineChart(canvas, _data.labels, _data.series[0].data);
        else if (chartId == "symptom_frequency_chart"){
            if(chartArr[1]) 
                chartArr[1].destroy();
            chartArr[1] = addBarChart(canvas, _data.labels, _data.series[0].data, '症狀');
        }
        else if (chartId == "medication_frequency_chart"){
            if(chartArr[2]) 
                chartArr[2].destroy();
            chartArr[2] = addBarChart(canvas, _data.labels, _data.series[0].data, '用藥');
        }
        else {

        }
    }
}

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
    if(!x_text)
        result.scales.x.title.display = false;
    if(!y_text)
        result.scales.y.title.display = false;
    
    return result;
}