import concurrent

import feedparser
import requests
import trafilatura
from newspaper import Article
from googlenewsdecoder import new_decoders
from concurrent.futures import ThreadPoolExecutor, as_completed
from trafilatura import fetch_url, extract

import time


proxy_config = {
    # 'http': 'http://127.0.0.1:7897' ,
    # 'https': 'http://127.0.0.1:7897'
    'http': 'http://127.0.0.1:10808' ,
    'https': 'http://127.0.0.1:10808'
}

# 1. 解析源
# rss_url = "http://feeds.bbci.co.uk/news/rss.xml"
rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

# 伪装头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# HEADERS = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#     'Accept-Language': 'en-US,en;q=0.5',
#     'Connection': 'keep-alive',
# }


def _fetch_content_by_tf(url):
    # 1. 下载网页
    session = requests.Session()
    session.proxies.update(proxy_config)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    try:
        # 4. 使用 requests 手动下载（不走 traFilatura 的下载逻辑）
        print("正在下载...")
        response = session.get(url, timeout=15)

        # 检查状态码
        if response.status_code == 200:
            print(f"下载成功，状态码: {response.status_code}")

            # 5. 将下载到的 HTML 直接传给 trafilatura.extract 进行解析
            # extract 函数接受 HTML 字符串作为输入
            content = trafilatura.extract(response.text)

            if content:
                print("解析成功！内容如下：")
                print(content)
            else:
                print("解析失败：extract 返回空，可能是动态加载页面")
        else:
            print(f"下载失败：HTTP 状态码 {response.status_code}")

    except Exception as e:
        print(f"发生错误: {e}")
def main():
    print(1)
    # news_list = _fetch_rss_by_feedparse(rss_url)
    # print(news_list)

    # get_google_news_single_thread(rss_url)
if __name__ == "__main__":
    main()
# 3. 遍历所有文章条目
# print(type(feed.entries))
# for idx,entry in enumerate(feed.entries[:10]):
#     print(f"第{idx+1}条新闻")
#     print("-" * 30)
#     print(f"标题: {entry.title}")
#     print(f"链接: {entry.link}")
#     # content = _fetch_article_content(entry.link)
#     _fetch_content_by_tf(entry.link)
#     # 有些源会有 published，有些没有，feedparser 会尽量解析
#     print(f"发布时间: {entry.get('published', 'N/A')}")
#     # 这里就用到了你之前问的 summary
#     print(f"摘要: {entry.summary[:50]}...")
