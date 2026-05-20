$(function(){
    $("#koreanVoice").hide();
    $("#submit").click(azureTranslate);
    $("#message").keypress(function (e) {
        if (e.which == 13) {
            azureTranslate();
        }
    });
    $("#koreanVoice").click(function () {
        $("#myAudio").attr("src", "");
        // add a random query string to the audio source to prevent caching
        $("#myAudio").attr("src", "/static/outputaudio.mp3?a=" + Math.random());
        $("#myAudio")[0].load();
        $("#myAudio")[0].play();
    });
});

function diaryProcess() {
    var date = $("#dateInput").val();
    var message = $("#message").val();
    var params = {
        date: date,
        message: message
    };
    $.post("/diary_process", params, function (data) {

    });
    //request url for diary result show
}

function erase_textarea() {
    $("#message").val("");
}

function azureTranslate() {
    $("#chineseText").empty();
    $("#koreanText").empty();
    $("#koreanVoice").hide();

    var message = $("#message").val();
    $("#chineseText").text(message);
    var params = {
        message: message
    };
    $.post("/azure_translate", params, function (data) {
        $("#koreanText").text(data);
        $("#koreanVoice").show();
    });
    $("#message").val("");
}