# 📰 Yahoo!ビジネスニュース要約ツール（Gemini × uv）

このツールは、Yahoo!ニュースのビジネスカテゴリの最新記事からタイトルに関連する内容だけを抽出し、Gemini APIを使って要約表示します。

---

## 🔧 セットアップ手順（uv使用）

### 0. uv のインストール（初回のみ）

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

インストール後、`uv` コマンドが使えることを確認してください：

```bash
uv --version
```

---

### 1. リポジトリをクローン

```bash
git clone https://github.com/your/repo.git
cd your/repo
```

---

### 2. `.env` ファイルを作成

プロジェクトルートに `.env` を作成し、以下のように記述：

```
GEMINI_API_KEY=your-api-key-here
```

---

### 3. 依存関係の同期（`pyproject.toml` と `uv.lock` がある場合）

```bash
uv sync
```

---

## ▶️ 実行方法

```bash
uv run python news.py
```

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
