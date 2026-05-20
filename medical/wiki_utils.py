'''
透過 wikipediaapi 搜尋藥名，並取得對應的英文維基百科連結

輸入: 藥物名稱 (drug_name)
輸出: 維基百科連結 (wiki_url)
'''

import wikipediaapi

def get_wiki_info(drug_name: str) -> dict:
    """
    使用 wikipediaapi 搜尋藥名，並取得對應的中文維基百科連結與主圖。
    """
    result = ""
    if not drug_name:
        return result

    # 初始化 Wikipedia API (指定中文語系 'zh')
    # 根據維基百科官方規範，必須在 user_agent 中聲明你的應用程式身分
    wiki = wikipediaapi.Wikipedia('ryan-agent-en', 'en')

    # 取得維基百科頁面物件
    page = wiki.page(drug_name)

    # 檢查該條目是否存在
    if not page.exists():
        # 如果精確匹配找不到，嘗試使用搜尋功能找最接近的條目
        # 注意：wikipediaapi 本身未直接封裝 search 列表，此處沿用更精準的 page 機制
        # 或是嘗試將常見藥物英文/中文去空格再查一次
        return result

    # 成功找到條目，直接透過物件屬性取得完整 URL
    result = page.fullurl
    title = page.title

    return result

# 獨立測試此模組
if __name__ == "__main__":
    # 測試常見藥物（如：阿斯匹靈）
    test_drug = input("請輸入要查詢的藥物名稱: ").strip()
    info = get_wiki_info(test_drug)
    print(f"藥物名稱: {test_drug}")
    print(f"維基連結: {info}")