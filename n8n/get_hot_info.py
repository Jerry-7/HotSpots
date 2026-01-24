import re

import requests
import yt_dlp
import json
import os

API_KEY = "AIzaSyCpEaSLCo8TYv40fwgfma9MJ38LuJkxvx0"
def search_videos(
    query=None,
    region="US",
    max_results=20,
    video_category_id=None,
    order="relevance",  # 可选: date, rating, viewCount, relevance, title
    video_duration=None,  # short (<4min), medium (4-20min), long (>20min)
    published_after=None,  # ISO 8601 string, e.g. "2025-12-01T00:00:00Z"
):
    """
    通用视频搜索函数，支持分类、关键词、排序等。
    如果 query=None 且未指定 category，则返回该地区最热门视频（兼容原功能）。
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "type": "video",
        "regionCode": region,
        "maxResults": min(max_results, 50),
        "key": API_KEY,
        "order": order,
    }

    # 如果有关键词，加入搜索
    if query:
        params["q"] = query

    # 分类筛选
    if video_category_id:
        params["videoCategoryId"] = str(video_category_id)

    # 视频时长筛选
    if video_duration in ("short", "medium", "long"):
        params["videoDuration"] = video_duration

    # 发布时间筛选
    if published_after:
        params["publishedAfter"] = published_after

    # 如果既无 query 也无 category，且 order 是默认值，则 fallback 到 mostPopular
    if not query and not video_category_id and order == "relevance":
        # 使用 videos.list + chart=mostPopular（仅此情况）
        return get_trending_fallback(region=region, max_results=max_results)

    # 否则使用 search 接口
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # 获取 videoId 列表
    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]

    if not video_ids:
        return []

    # 批量获取详细信息（含 statistics）
    details = get_video_details(video_ids)
    return details


def get_video_subtitles(video_url, languages=None):
    """
    获取视频字幕
    :param video_url: 视频URL
    :param languages: 语言列表，例如 ['en', 'zh-CN']，如果为None则获取所有可用字幕
    :return: 字幕字典，键为语言代码，值为字幕文本
    """
    if languages is None:
        languages = ['en', 'zh-CN', 'zh-TW', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 'ar']

    # 配置yt-dlp选项，增加网络请求的稳定性
    ydl_opts = {
        'writesubtitles': True,
        'subtitleslangs': languages,
        'skip_download': True,  # 不下载视频
        'quiet': True,
        'ignoreerrors': True,
        'socket_timeout': 30,  # 增加套接字超时
        'retries': 3,  # 重试次数
        'fragment_retries': 3,  # 片段重试次数
        'file_access_retries': 3,  # 文件访问重试次数
        'nocheckcertificate': True,  # 忽略证书验证
    }

    subtitles = {}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # 检查是否有手动字幕（优先级更高）
            if 'subtitles' in info and info['subtitles']:
                print(f"发现手动字幕: {list(info['subtitles'].keys())}")
                for lang, sub_formats in info['subtitles'].items():
                    if lang in languages:
                        # 获取最高质量的字幕格式
                        if sub_formats:
                            try:
                                sub_url = sub_formats[0]['url']
                                response = requests.get(sub_url, timeout=30, verify=False)  # 禁用SSL验证
                                if response.status_code == 200:
                                    # 解析XML格式的字幕
                                    xml_content = response.text
                                    subtitles[lang] = parse_xml_captions(xml_content)
                            except Exception as e:
                                print(f"获取手动字幕 {lang} 时出错: {e}")

            # 如果没有手动字幕，再检查自动字幕
            if not subtitles and 'automatic_captions' in info and info['automatic_captions']:
                print(f"发现自动字幕: {list(info['automatic_captions'].keys())}")
                for lang, captions in info['automatic_captions'].items():
                    if lang in languages:
                        # 获取最高质量的字幕格式
                        if captions:
                            try:
                                caption_url = captions[0]['url']
                                response = requests.get(caption_url, timeout=30, verify=False)  # 禁用SSL验证
                                if response.status_code == 200:
                                    # 解析XML格式的字幕
                                    xml_content = response.text
                                    subtitles[lang] = parse_xml_captions(xml_content)
                            except Exception as e:
                                print(f"获取自动字幕 {lang} 时出错: {e}")
    except Exception as e:
        print(f"获取字幕时发生错误: {e}")
        # 尝试使用备用方法
        subtitles = get_subtitles_fallback(video_url, languages)

    return subtitles


def get_subtitles_fallback(video_url, languages):
    """
    备用字幕获取方法
    """
    print("使用备用方法获取字幕...")
    subtitles = {}

    try:
        # 尝试使用yt-dlp直接获取字幕文本
        ydl_opts = {
            'writesubtitles': False,
            'writeautomaticsub': False,
            'skip_download': True,
            'quiet': True,
            'ignoreerrors': True,
            'socket_timeout': 30,
            'retries': 3,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # 获取视频ID
            video_id = info.get('id', '')
            if not video_id:
                return {}

            # 尝试通过API获取字幕
            for lang in languages:
                try:
                    # 尝试获取手动字幕
                    subtitle_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang={lang}&fmt=json3"
                    response = requests.get(subtitle_url, timeout=30, verify=False)
                    if response.status_code == 200:
                        try:
                            subtitle_data = response.json()
                            if 'events' in subtitle_data:
                                text = ' '.join([event.get('segs', [{}])[0].get('utf8', '')
                                                 for event in subtitle_data.get('events', [])
                                                 if event.get('segs')])
                                if text.strip():
                                    subtitles[lang] = text
                                    print(f"成功获取 {lang} 字幕")
                                    break
                        except:
                            pass

                    # 如果手动字幕失败，尝试自动字幕
                    if lang not in subtitles:
                        auto_subtitle_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang={lang}&fmt=json3&kind=asr"
                        response = requests.get(auto_subtitle_url, timeout=30, verify=False)
                        if response.status_code == 200:
                            try:
                                subtitle_data = response.json()
                                if 'events' in subtitle_data:
                                    text = ' '.join([event.get('segs', [{}])[0].get('utf8', '')
                                                     for event in subtitle_data.get('events', [])
                                                     if event.get('segs')])
                                    if text.strip():
                                        subtitles[lang] = text
                                        print(f"成功获取 {lang} 自动字幕")
                                        break
                            except:
                                pass
                except Exception as e:
                    print(f"获取 {lang} 字幕时出错: {e}")
                    continue
    except Exception as e:
        print(f"备用方法也失败: {e}")

    return subtitles


def parse_xml_captions(xml_content):
    """
    解析XML格式的YouTube字幕
    :param xml_content: XML格式的字幕内容
    :return: 纯文本字幕
    """
    # 使用正则表达式提取字幕文本
    # 匹配 <text start="..." dur="...">内容</text> 格式
    pattern = r'<text[^>]*>(.*?)</text>'
    matches = re.findall(pattern, xml_content, re.DOTALL)

    # 清理和合并字幕文本
    captions = []
    for match in matches:
        # 解码HTML实体
        caption_text = match.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;',
                                                                                                     '"').replace(
            '&#39;', "'")
        captions.append(caption_text.strip())

    return '\n'.join(caption for caption in captions if caption)


def get_video_transcript(video_url, languages=None):
    """
    获取视频完整转录文本
    :param video_url: 视频URL
    :param languages: 语言列表，例如 ['en', 'zh-CN']，如果为None则获取所有可用字幕
    :return: 转录文本字典
    """
    subtitles = get_video_subtitles(video_url, languages)
    transcript = {}

    for lang, sub_text in subtitles.items():
        transcript[lang] = {
            'text': sub_text,
            'word_count': len(sub_text.split()),
            'char_count': len(sub_text)
        }

    return transcript


def save_subtitles_to_file(video_url, output_dir="./subtitles", languages=None, video_title=None):
    """
    将视频字幕保存到本地文件
    :param video_url: 视频URL
    :param output_dir: 输出目录
    :param languages: 语言列表
    :param video_title: 视频标题（用于文件名）
    :return: 保存的文件路径列表
    """
    if languages is None:
        languages = ['en', 'zh-CN', 'zh-TW', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 'ar']

    os.makedirs(output_dir, exist_ok=True)

    # 获取视频ID
    video_id = video_url.split("v=")[1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]

    # 如果没有提供视频标题，使用视频ID
    if not video_title:
        video_title = f"video_{video_id}"

    # 清理文件名
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)

    # 获取字幕
    transcript = get_video_transcript(video_url, languages)

    saved_files = []

    for lang, data in transcript.items():
        if data['text']:  # 只保存有内容的字幕
            # 创建文件名
            filename = f"{safe_title}_{lang}.txt"
            filepath = os.path.join(output_dir, filename)

            # 保存字幕到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"视频标题: {video_title}\n")
                f.write(f"视频URL: {video_url}\n")
                f.write(f"语言: {lang}\n")
                f.write(f"字数: {data['word_count']}\n")
                f.write(f"字符数: {data['char_count']}\n")
                f.write("-" * 50 + "\n")
                f.write(data['text'])

            saved_files.append(filepath)
            print(f"字幕已保存到: {filepath}")

    return saved_files


def save_multiple_subtitles_to_files(videos, output_dir="./subtitles", languages=None):
    """
    批量保存多个视频的字幕到本地文件
    :param videos: 视频列表，每个视频应包含title和url
    :param output_dir: 输出目录
    :param languages: 语言列表
    :return: 保存的文件路径列表
    """
    all_saved_files = []

    for i, video in enumerate(videos):
        print(f"\n正在处理第 {i + 1}/{len(videos)} 个视频: {video['title']}")
        try:
            saved_files = save_subtitles_to_file(
                video_url=video['url'],
                output_dir=output_dir,
                languages=languages,
                video_title=video['title']
            )
            all_saved_files.extend(saved_files)
        except Exception as e:
            print(f"处理视频 {video['title']} 时出错: {e}")

    return all_saved_files

def get_trending_fallback(region="US", max_results=20):
    """原 get_trending 功能，用于无搜索条件时的热门榜单"""
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": max_results,
        "key": API_KEY
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("items", []):
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        results.append({
            "videoId": item["id"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "publishedAt": snippet["publishedAt"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "viewCount": stats.get("viewCount"),
            "likeCount": stats.get("likeCount")
        })
    return results

def get_video_details(video_ids):
    """根据 videoId 列表批量获取详细信息（含统计数据）"""
    if not video_ids:
        return []
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids[:50]),  # YouTube 最多一次查 50 个
        "key": API_KEY
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("items", []):
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        results.append({
            "videoId": item["id"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "publishedAt": snippet["publishedAt"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "viewCount": stats.get("viewCount"),
            "likeCount": stats.get("likeCount")
        })
    return results


def get_trending(
    region="US",
    max_results=50
):
    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": max_results,
        "key": API_KEY
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()

    data = resp.json()

    results = []
    for item in data.get("items", []):
        snippet = item["snippet"]
        stats = item.get("statistics", {})

        results.append({
            "videoId": item["id"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "publishedAt": snippet["publishedAt"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "viewCount": stats.get("viewCount"),
            "likeCount": stats.get("likeCount")
        })

    return results

def download_videos(video_urls, output_dir="./downloads"):
    """使用 yt-dlp 下载视频列表"""
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s'),
        'format': 'best[ext=mp4]/best',  # 简化格式选择，避免合并问题
        'noplaylist': True,
        'quiet': False,  # 设为 True 可静默
        'ignoreerrors': True,  # 跳过无法下载的视频
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls']
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(video_urls)

if __name__ == "__main__":
    # trending = get_trending(region="US", max_results=20)
    # print(json.dumps(trending, ensure_ascii=False, indent=2))
    # 提取所有视频 URL
    # urls = [item["url"] for item in trending]

    # 下载视频
    # print(f"\n开始下载 {len(urls)} 个视频到 ./downloads/ 目录...")
    # download_videos(urls)
    saved_files = save_subtitles_to_file(
        video_url="https://www.youtube.com/watch?v=IxxIwF9i1qc",
        output_dir="./subtitles",
        languages=['en', 'zh-CN'],
        video_title="Me And My Friend Went Ghost Hunting…"
    )
    # 获取视频字幕
    # if trending:
    #     print(f"\n保存视频 '{trending[0]['title']}' 的字幕到本地文件:")
    #     video_url = trending[0]['url']
    #     video_title = trending[0]['title']
    #
    #     saved_files = save_subtitles_to_file(
    #         video_url=video_url,
    #         output_dir="./subtitles",
    #         languages=['en', 'zh-CN'],
    #         video_title=video_title
    #     )
    #
    #     print(f"\n✅ 已保存 {len(saved_files)} 个字幕文件")
    # else:
    #     print("\n❌ 没有找到可下载的视频")
