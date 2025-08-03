# 📰 Yahoo!ビジネスニュース要約ツール（Gemini × uv）

このツールは、Yahoo!ニュースのビジネスカテゴリの最新記事からタイトルに関連する内容だけを抽出し、Gemini APIを使って要約表示します。

---

## 🔧 セットアップ手順（uv使用）

### 1. リポジトリをクローン

```bash
git clone https://github.com/your/repo.git
cd your/repo
```

### 2. uv初期化 & 依存追加

```bash
uv init .
uv add python-dotenv feedparser requests beautifulsoup4 pydantic pydantic-ai
```

### 3. `.env` ファイルを作成

プロジェクトルートに `.env` を作成し、以下のように記述：

```
GEMINI_API_KEY=your-api-key-here
```

---

## ▶️ 実行方法

```bash
uv run python main.py
```

> 💡 `main.py` は、実際のスクリプト名に応じて変更してください。

---

## 📦 使用ライブラリ

- `feedparser` - RSSフィード取得
- `requests` - HTMLページ取得
- `beautifulsoup4` - HTML解析
- `pydantic`, `pydantic-ai` - Gemini APIとのやりとり
- `python-dotenv` - `.env` の環境変数読み込み

---

## 💡 補足

- `uv` は `pip`, `venv`, `pip-tools` の代替として使えるパッケージ管理＆仮想環境ツールです。
- Geminiモデルには `"gemini-2.5-flash"` を使用しています。
