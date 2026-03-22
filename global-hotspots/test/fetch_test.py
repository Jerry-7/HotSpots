import feedparser
import requests
import trafilatura
import time
import urllib.request
from googlenewsdecoder import new_decoders

# ============================================================
# 代理配置
# ============================================================

# HTTP/HTTPS 代理
PROXY_CONFIG = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

# SOCKS5 代理（需要 pip install requests[socks] 或 pip install PySocks）
# PROXY_CONFIG = {
#     'http': 'socks5h://127.0.0.1:1080',
#     'https': 'socks5h://127.0.0.1:1080',
# }

# 带认证的代理
# PROXY_CONFIG = {
#     'http': 'http://user:password@proxy_host:port',
#     'https': 'http://user:password@proxy_host:port',
# }

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/125.0.0.0 Safari/537.36'
}

TIMEOUT = 15


# ============================================================
# 1. 通过代理获取 RSS Feed
# ============================================================
def fetch_rss_with_proxy(rss_url):
    """通过代理获取 RSS 内容，再用 feedparser 解析"""

    # 方法 A：先用 requests 下载，再交给 feedparser 解析
    resp = requests.get(
        rss_url,
        headers=HEADERS,
        proxies=PROXY_CONFIG,
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)

    # 方法 B：设置全局代理让 feedparser 直接用（备用）
    # import os
    # os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    # os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    # feed = feedparser.parse(rss_url)

    return feed


# ============================================================
# 2. 解码 Google News 重定向链接（获取真实 URL）
# ============================================================
def decode_google_news_url(google_url):
    """多种方式尝试解码 Google News URL"""

    # 方法 1：使用 googlenewsdecoder
    try:
        decoded = new_decoders.decode_url(google_url)
        real_url = decoded.get("decoded_url")
        if real_url:
            return real_url
    except Exception as e:
        print(f"  [decoder失败]: {e}")

    # 方法 2：通过代理跟踪 HTTP 重定向
    try:
        resp = requests.get(
            google_url,
            headers=HEADERS,
            proxies=PROXY_CONFIG,
            allow_redirects=True,
            timeout=TIMEOUT
        )
        if resp.url != google_url:
            return resp.url
    except Exception as e:
        print(f"  [重定向失败]: {e}")

    # 方法 3：HEAD 请求（更轻量）
    try:
        resp = requests.head(
            google_url,
            headers=HEADERS,
            proxies=PROXY_CONFIG,
            allow_redirects=True,
            timeout=TIMEOUT
        )
        if resp.url != google_url:
            return resp.url
    except Exception as e:
        print(f"  [HEAD请求失败]: {e}")

    # 方法 4：手动解析 Base64 编码
    try:
        import base64, re
        match = re.search(r'articles/(.*?)(\?|$)', google_url)
        if match:
            encoded = match.group(1)
            padding = 4 - len(encoded) % 4
            if padding != 4:
                encoded += '=' * padding
            decoded_bytes = base64.urlsafe_b64decode(encoded).decode('latin-1')
            urls = re.findall(r'https?://[^\s"<>\x00-\x1f]+', decoded_bytes)
            if urls:
                return urls[0]
    except Exception as e:
        print(f"  [Base64解码失败]: {e}")

    return google_url


# ============================================================
# 3. 通过代理提取原文内容
# ============================================================
def extract_article_with_proxy(url):
    """通过代理下载网页并提取正文"""

    # 方法 A：使用 trafilatura（推荐）
    try:
        # trafilatura 不直接支持代理参数，所以先用 requests 下载
        resp = requests.get(
            url,
            headers=HEADERS,
            proxies=PROXY_CONFIG,
            timeout=TIMEOUT
        )
        resp.raise_for_status()

        text = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=True,
            favor_precision=True
        )
        if text:
            return text
    except Exception as e:
        print(f"  [trafilatura失败]: {e}")

    # 方法 B：使用 newspaper3k（备用）
    try:
        from newspaper import Article, Config

        config = Config()
        config.browser_user_agent = HEADERS['User-Agent']
        config.proxies = PROXY_CONFIG  # newspaper3k 原生支持代理
        config.request_timeout = TIMEOUT

        article = Article(url, config=config)
        article.download()
        article.parse()

        if article.text:
            return article.text
    except Exception as e:
        print(f"  [newspaper3k失败]: {e}")

    # 方法 C：使用 readability（备用）
    try:
        from readability import Document

        resp = requests.get(
            url,
            headers=HEADERS,
            proxies=PROXY_CONFIG,
            timeout=TIMEOUT
        )
        doc = Document(resp.text)

        # 去除 HTML 标签
        import re
        content = re.sub(r'<[^>]+>', '', doc.summary())
        content = re.sub(r'\s+', ' ', content).strip()
        if content:
            return content
    except Exception as e:
        print(f"  [readability失败]: {e}")

    return None


# ============================================================
# 4. 主函数：完整流程
# ============================================================
def get_google_news_articles(rss_url, max_articles=10, delay=2):
    """
    完整流程：RSS解析 → URL解码 → 原文提取

    Args:
        rss_url: Google News RSS 地址
        max_articles: 最多获取文章数
        delay: 每篇文章之间的延迟（秒），避免被封
    """

    print(f"📡 正在通过代理获取 RSS Feed...")
    print(f"   代理: {PROXY_CONFIG.get('https', PROXY_CONFIG.get('http'))}")
    print()

    feed = fetch_rss_with_proxy(rss_url)

    print(f"📰 共发现 {len(feed.entries)} 条新闻，获取前 {max_articles} 条\n")
    print("=" * 80)

    articles = []

    for i, entry in enumerate(feed.entries[:max_articles]):
        print(f"\n[{i + 1}/{max_articles}] {entry.title}")
        print(f"  发布时间: {entry.get('published', 'N/A')}")

        # Step 1: 解码 URL
        real_url = decode_google_news_url(entry.link)
        print(f"  原文链接: {real_url}")

        # Step 2: 提取正文
        content = extract_article_with_proxy(real_url)

        if content:
            preview = content[:300].replace('\n', ' ')
            print(f"  ✅ 内容预览: {preview}...")
        else:
            print(f"  ❌ 无法提取内容（可能有付费墙）")

        articles.append({
            'title': entry.title,
            'url': real_url,
            'google_url': entry.link,
            'published': entry.get('published', ''),
            'source': entry.get('source', {}).get('title', ''),
            'content': content
        })

        # 延迟，避免被反爬
        if i < max_articles - 1:
            time.sleep(delay)

    print("\n" + "=" * 80)

    # 统计
    success = sum(1 for a in articles if a['content'])
    print(f"\n📊 结果统计: 成功 {success}/{len(articles)} 篇")

    return articles


# ============================================================
# 5. 运行
# ============================================================
if __name__ == '__main__':
    rss_url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'

    # 也可以用特定主题的 RSS
    # rss_url = 'https://news.google.com/rss/search?q=AI&hl=en-US&gl=US&ceid=US:en'
    # rss_url = 'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en'  # Technology

    articles = get_google_news_articles(
        rss_url,
        max_articles=5,
        delay=2
    )

    # 保存结果到 JSON
    import json

    with open('news_articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("\n💾 结果已保存到 news_articles.json")