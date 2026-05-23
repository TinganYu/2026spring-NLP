$(function(){
    $("#analyze").click(diaryProcess);
    $("#erase").click(function() {
        $("#message").val("");
    });
    $("#medical-btn").click(() => switchTab("medical"));
    $("#diary-btn").click(() => switchTab("diary"));
    $("#graph-btn").click(() => switchTab("graph"));
});

function switchTab(tab_name) {
    const nowTab = document.querySelector(".tab.select");
    if (nowTab.id == tab_name+'-btn')
        return;
    else
        window.location.replace("/"+tab_name);
}