from flask import Flask, render_template, jsonify
import asyncio
from news_fetcher import fetch_articles_for_web

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/fetch_news")
def fetch_news_api():
    articles = asyncio.run(fetch_articles_for_web())
    return jsonify(articles)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
