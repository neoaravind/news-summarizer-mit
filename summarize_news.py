
import feedparser
import json
import os
import re

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dotenv import load_dotenv
from sarvamai import SarvamAI

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

RSS_URL = "https://www.technologyreview.com/feed/"
NUMBER_OF_ARTICLES = 5

from datetime import timedelta

IST = timezone(timedelta(hours=5, minutes=30))

load_dotenv()

API_KEY = os.getenv("SARVAM_API_KEY")
MODEL = os.getenv("SARVAM_MODEL", "sarvam-105b")

if not API_KEY:
    raise ValueError("SARVAM_API_KEY is missing from .env")

client = SarvamAI(
    api_subscription_key=API_KEY
)


# --------------------------------------------------
# 2. FETCH RSS FEED
# --------------------------------------------------

print("Fetching MIT Technology Review RSS feed...")

feed = feedparser.parse(RSS_URL)

if feed.bozo and not feed.entries:
    raise RuntimeError("Unable to read RSS feed.")

print("Articles available:", len(feed.entries))


# --------------------------------------------------
# 3. EXTRACT ARTICLE INFORMATION
# --------------------------------------------------

articles = []

for entry in feed.entries:

    published = entry.get("published_parsed")

    if not published:
        continue

    published_utc = datetime(
        *published[:6],
        tzinfo=timezone.utc
    )

    published_ist = published_utc.astimezone(IST)

    # Extract full HTML content
    content_items = entry.get("content", [])

    html_content = "\n".join(
        item.get("value", "")
        for item in content_items
    )

    # Convert HTML to plain text
    soup = BeautifulSoup(html_content, "html.parser")

    article_text = soup.get_text(
        separator="\n",
        strip=True
    )

    article_text = re.sub(
        r"\n{3,}",
        "\n\n",
        article_text
    )

    if not article_text.strip():
        continue

    categories = [
        tag.get("term", "")
        for tag in entry.get("tags", [])
        if tag.get("term")
    ]

    articles.append({
        "title": entry.get("title", ""),
        "url": entry.get("link", ""),
        "author": entry.get("author", ""),
        "published_date": published_ist.strftime("%Y-%m-%d"),
        "published_time": published_ist.strftime("%H:%M:%S"),
        "categories": categories,
        "article_text": article_text
    })


# --------------------------------------------------
# 4. SELECT FIVE LATEST ARTICLES
# --------------------------------------------------

articles.sort(
    key=lambda x: (
        x["published_date"],
        x["published_time"]
    ),
    reverse=True
)

selected_articles = articles[:NUMBER_OF_ARTICLES]

print("\nArticles selected:", len(selected_articles))


# --------------------------------------------------
# 5. GENERATE SUMMARIES USING SARVAM AI
# --------------------------------------------------

def summarize_article(article):

    prompt = f"""
    You are an expert news analyst.

    Analyze the following article and prepare a useful
    and concise news summary.

    TITLE:
    {article['title']}

    ARTICLE:
    {article['article_text']}

    Follow this exact structure:

    Summary:
    Write one concise paragraph explaining the complete
    story, its main argument and important developments.

    Key Takeaways:
    Provide 3 to 5 important facts, findings or developments.

    Why It Matters:
    Explain why this story is relevant to readers.

    IMPORTANT INSTRUCTIONS:

    1. Use only information present in the article.
    2. Do not invent facts or introduce outside information.
    3. Preserve important numbers, names and dates.
    4. Distinguish facts from opinions and projections.
    5. Avoid repeating the same information.
    6. Write in clear, simple English.
    7. Make the summary understandable without reading
       the original article.
    """

    response = client.chat.completions(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        reasoning_effort=None,
        max_tokens=1200
    )

    return response.choices[0].message.content


# Process each article

for index, article in enumerate(selected_articles, start=1):

    print(f"\nSummarizing article {index}:")
    print(article["title"])

    try:

        summary = summarize_article(article)

        if not summary:
            raise ValueError("Sarvam returned empty content.")

        article["ai_summary"] = summary

        print("Summary generated successfully.")

    except Exception as error:

        article["ai_summary"] = ""

        print("Summarization failed:", error)


# --------------------------------------------------
# 6. SAVE EXTRACTED ARTICLES
# --------------------------------------------------

with open(
    "latest_articles.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        selected_articles,
        file,
        indent=4,
        ensure_ascii=False
    )


# --------------------------------------------------
# 7. GENERATE NEWS BRIEFING
# --------------------------------------------------

with open(
    "news_briefing.md",
    "w",
    encoding="utf-8"
) as file:

    file.write("# MIT Technology Review - News Briefing\n\n")

    file.write(
        f"Generated: {datetime.now(IST).strftime('%d %B %Y, %H:%M IST')}\n\n"
    )

    file.write("---\n\n")

    for index, article in enumerate(selected_articles, start=1):

        file.write(f"## {index}. {article['title']}\n\n")

        file.write(f"**Author:** {article['author']}\n\n")

        file.write(
            f"**Published:** {article['published_date']} "
            f"{article['published_time']} IST\n\n"
        )

        file.write(
            f"**Categories:** {', '.join(article['categories'])}\n\n"
        )

        file.write(
            f"**Original article:** {article['url']}\n\n"
        )

        file.write(
            article["ai_summary"] or "Summary unavailable."
        )

        file.write("\n\n---\n\n")


# --------------------------------------------------
# 8. FINAL REPORT
# --------------------------------------------------

successful = sum(
    1 for article in selected_articles
    if article["ai_summary"]
)

print("\nNEWS SUMMARIZER COMPLETED")
print("-------------------------")
print("Articles extracted:", len(selected_articles))
print("Successful summaries:", successful)
print("Failed summaries:", len(selected_articles) - successful)
print("Extracted data: latest_articles.json")
print("News briefing: news_briefing.md")
