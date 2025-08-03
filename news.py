import feedparser
import requests
from bs4 import BeautifulSoup

RSS_URL = "https://news.yahoo.co.jp/rss/topics/business.xml"

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
                break  # 関連記事やPR領域で終了

        return "\n".join(paragraphs)

    except Exception as e:
        return f"⚠️ Yahoo本文取得失敗: {e}"

def extract_external_full_text(url: str) -> str:
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        raw_paragraphs = soup.find_all("p")

        valid_lines = []
        for p in raw_paragraphs:
            text = p.get_text().strip()
            if text:
                valid_lines.append(text)

        # 最後の "Copyright" などを検出してそこから10段落分除去
        cut_index = None
        for i in reversed(range(len(valid_lines))):
            last_line = valid_lines[i]
            if (
                last_line.startswith("Copyright") or
                last_line.startswith("Copyright ©") or
                last_line.endswith("無断転載を禁じます。") or
                last_line.endswith("無断転載を禁じます")
            ):
                cut_index = i
                break

        if cut_index is not None:
            keep_up_to = max(cut_index - 10, 0)
            valid_lines = valid_lines[:keep_up_to]

        return "\n".join(valid_lines)

    except Exception as e:
        return f"⚠️ 外部記事取得失敗: {e}"

def fetch_yahoo_full_articles(max_items=5):
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

            # 「記事全文を読む」リンクを探す
            external_link = soup.find("a", string="記事全文を読む")

            if external_link and external_link.has_attr("href"):
                full_url = external_link["href"]
                print(f"   🔗 外部全文リンク: {full_url}")
                external_text = extract_external_full_text(full_url)
                print(f"   📖 本文抜粋（外部）:\n{external_text}...\n")
            else:
                print("   ℹ️ 外部記事リンクがないため、Yahoo本文を抽出します")
                yahoo_text = extract_yahoo_full_text(entry.link)
                if yahoo_text:
                    print(f"   📖 本文抜粋（Yahoo内）:\n{yahoo_text}...\n")
                else:
                    print("   ⚠️ Yahoo本文も取得できませんでした")

        except Exception as e:
            print(f"   ⚠️ 全体処理中にエラー: {e}")

        print("-" * 100)

if __name__ == "__main__":
    fetch_yahoo_full_articles()
