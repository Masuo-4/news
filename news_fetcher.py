import os
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
import asyncio

# ✅ RSS URL定義
RSS_URL = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"

# ✅ Gemini設定（.env読み込み）
load_dotenv()
model = GeminiModel("gemini-2.5-flash")
agent = Agent(model=model, output_type=BaseModel)

# ✅ タイトル関連抽出（AI処理）
class Summary(BaseModel):
    filtered_text: str

agent = Agent(model=model, output_type=Summary)

async def extract_title_related_content(title: str, full_text: str) -> str:
    prompt = f"""
以下はニュース記事の全文です。その中から「{title}」というタイトルに関係ない部分を削除してください。
他のニュース見出し、関連情報、広告・著作権情報なども削除してください。次に、残ったタイトルに関係ある内容を、要約して出力してください。

全文:
{full_text}
"""
    result = await agent.run(prompt)
    return result.output.filtered_text

# ✅ Yahoo記事HTMLから本文抽出
def extract_yahoo_full_text(url: str) -> str:
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        article_body = soup.select_one("article")
        if not article_body:
            return ""
        paragraphs = []
        for tag in article_body.children:
            if tag.name == "p":
                text = tag.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            elif tag.name in {"div", "section"}:
                break
        return "\n".join(paragraphs)
    except Exception as e:
        return f"⚠️ Yahoo本文取得失敗: {e}"

# ✅ 外部記事（全文取得・複数ページ対応）
def extract_external_full_text(url: str, max_pages: int = 5) -> str:
    try:
        all_paragraphs = []
        parsed_url = urlparse(url)
        base_query = parse_qs(parsed_url.query)

        for page_num in range(1, max_pages + 1):
            query = base_query.copy()
            if page_num > 1:
                query["page"] = [str(page_num)]
            query_str = urlencode(query, doseq=True)
            page_url = urlunparse(parsed_url._replace(query=query_str))

            res = requests.get(page_url, timeout=5)
            if res.status_code >= 400:
                break

            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all("p")
            if not paragraphs:
                break

            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    all_paragraphs.append(text)

        cut_index = None
        for i in reversed(range(len(all_paragraphs))):
            last_line = all_paragraphs[i]
            if (
                last_line.startswith("Copyright") or
                last_line.startswith("Copyright ©") or
                last_line.endswith("無断転載を禁じます") or
                last_line.endswith("無断転載を禁じます。")
            ):
                cut_index = i
                break

        if cut_index is not None:
            keep_up_to = max(cut_index - 10, 0)
            all_paragraphs = all_paragraphs[:keep_up_to]

        return "\n".join(all_paragraphs)

    except Exception as e:
        return f"⚠️ 外部記事取得失敗: {e}"

# ✅ メイン処理：Flask側から呼び出される非同期関数
async def fetch_articles_for_web(max_items=10):
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return []

    results = []
    for entry in feed.entries[:max_items]:
        try:
            title = entry.title
            link = entry.link

            res = requests.get(link, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            external_link = soup.find("a", string="記事全文を読む")

            if external_link and external_link.has_attr("href"):
                full_url = external_link["href"]
                full_text = extract_external_full_text(full_url)
                related_text = await extract_title_related_content(title, full_text)
                results.append({
                    "title": title,
                    "yahoo_link": link,
                    "external_link": full_url,
                    "content": related_text,
                })
            else:
                yahoo_text = extract_yahoo_full_text(link)
                related_text = await extract_title_related_content(title, yahoo_text)
                results.append({
                    "title": title,
                    "yahoo_link": link,
                    "external_link": None,
                    "content": related_text,
                })
        except Exception as e:
            results.append({
                "title": entry.title,
                "yahoo_link": entry.link,
                "external_link": None,
                "content": f"[エラー発生] {e}"
            })
    return results
