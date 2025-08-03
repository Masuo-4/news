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

# =======================
# 設定・初期化
# =======================
load_dotenv()
RSS_URL = "https://news.yahoo.co.jp/rss/topics/business.xml"

class Summary(BaseModel):
    filtered_text: str

model = GeminiModel("gemini-2.5-flash")
agent = Agent(model=model, output_type=Summary)

# =======================
# Geminiでタイトル関連の内容だけを抽出
# =======================
async def extract_title_related_content(title: str, full_text: str) -> str:
    prompt = f"""
以下はニュース記事の全文です。その中から「{title}」というタイトルに関係ない部分を削除して表示してください。
他のニュース見出し、関連情報、広告・著作権情報などは除外してください。タイトルに関係ある部分は省略せずに表示してください。

全文:
{full_text}
"""
    result = await agent.run(prompt)
    return result.output.filtered_text

# =======================
# Yahoo記事抽出
# =======================
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
                break  # 関連記事などで終了

        return "\n".join(paragraphs)
    except Exception as e:
        return f"⚠️ Yahoo本文取得失敗: {e}"

# =======================
# 外部全文抽出（?page=2にも対応、著作権末尾10段落カット）
# =======================
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

        # 著作権表記のカット
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

# =======================
# メイン処理
# =======================
async def fetch_yahoo_full_articles(max_items=4):
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("❌ RSSの取得に失敗しました。")
        return

    for i, entry in enumerate(feed.entries[:max_items], 1):
        print(f"{i}. 📰 {entry.title}")
        print(f"   📎 Yahoo URL: {entry.link}")

        try:
            res = requests.get(entry.link, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            external_link = soup.find("a", string="記事全文を読む")

            if external_link and external_link.has_attr("href"):
                full_url = external_link["href"]
                print(f"   🔗 外部全文リンク: {full_url}")
                external_text = extract_external_full_text(full_url)
                related_text = await extract_title_related_content(entry.title, external_text)
                print(f"🎯 タイトルに関係する内容（外部）:\n{related_text}\n")
            else:
                print("   ℹ️ 外部記事リンクがないため、Yahoo本文を抽出します")
                yahoo_text = extract_yahoo_full_text(entry.link)
                related_text = await extract_title_related_content(entry.title, yahoo_text)
                print(f"🎯 タイトルに関係する内容（Yahoo）:\n{related_text}\n")

        except Exception as e:
            print(f"   ⚠️ 全体処理中にエラー: {e}")

        print("-" * 100)

if __name__ == "__main__":
    asyncio.run(fetch_yahoo_full_articles())
