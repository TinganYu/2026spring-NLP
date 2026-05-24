$(function(){
    $("#erase").click(function() {
        $("#message").val("");
    });
    $("#medical-btn").click(() => switchTab("medical"));
    $("#diary-btn").click(() => switchTab("diary"));
    $("#graph-btn").click(() => switchTab("graph"));
});

function switchTab(tab_name) {
    const nowTab = $(".tab.select");
    if (nowTab.attr("id") == tab_name+'-btn')
        return;
    else
        window.location.replace("/"+tab_name);
}