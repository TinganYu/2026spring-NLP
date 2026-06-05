$(function(){
    // tab切換
    $("#medical-btn").click(() => switchTab("medical"));
    $("#diary-btn").click(() => switchTab("diary"));
    $("#graph-btn").click(() => switchTab("graph"));
});

// 切換至點選tab
function switchTab(tab_name) {
    const nowTab = $(".tab.select");
    if (nowTab.attr("id") == tab_name+'-btn')   // 如果現在就在這個tab，不需要切換
        return;
    else
        window.location.replace("/"+tab_name);
}