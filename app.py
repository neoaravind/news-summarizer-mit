
import streamlit as st
import os

# Load cloud secrets into environment variables
if "SARVAM_API_KEY" in st.secrets:
    os.environ["SARVAM_API_KEY"] = st.secrets["SARVAM_API_KEY"]

if "SARVAM_MODEL" in st.secrets:
    os.environ["SARVAM_MODEL"] = st.secrets["SARVAM_MODEL"]

import subprocess
import sys
import json
from pathlib import Path

# Project files
BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "summarize_news.py"
JSON_PATH = BASE_DIR / "latest_articles.json"

# Page configuration
st.set_page_config(
    page_title="Morning Intelligence",
    page_icon="📰",
    layout="wide"
)

# Page heading
st.title("📰 Morning Intelligence")
st.caption("Your daily technology news briefing")

st.divider()

# Button to run the summarizer
if st.button("Fetch and summarise latest news", type="primary"):

    with st.spinner("Fetching articles and generating summaries..."):

        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

            if result.returncode != 0:
                st.error("Something went wrong while generating the summaries.")
                st.code(result.stderr)
            elif not JSON_PATH.exists():
                st.error("The summarizer finished, but the JSON file was not found.")
            else:
                with open(JSON_PATH, "r", encoding="utf-8") as file:
                    st.session_state.articles = json.load(file)

                st.success("Your latest five summaries are ready!")

        except Exception as error:
            st.error(f"An error occurred: {error}")

# Display articles
articles = st.session_state.get("articles", [])

# Temporary debugging information
with st.expander("Debug information"):
    st.write("Number of articles:", len(articles))

    if articles:
        st.write("Available JSON fields:")
        st.write(list(articles[0].keys()))

        st.write("First article summary:")
        st.write(repr(articles[0].get("ai_summary")))

        st.write(
            "Summary length:",
            len(str(articles[0].get("ai_summary", "")))
        )

if articles:

    st.subheader(f"Latest {len(articles)} Articles")

    for index, article in enumerate(articles, start=1):

        title = article.get("title", "Untitled article")
        author = article.get("author", "Unknown author")
        published = article.get("published_ist", "Date unavailable")
        url = article.get("url", article.get("link", ""))
        summary = article.get("ai_summary", "Summary unavailable")
        categories = article.get("categories", article.get("tags", []))

        with st.expander(f"{index}. {title}", expanded=(index == 1)):

            st.caption(f"Author: {author} | Published: {published}")

            if categories:
                if isinstance(categories, list):
                    st.caption("Categories: " + ", ".join(
                        str(item) for item in categories
                    ))
                else:
                    st.caption(f"Categories: {categories}")

            st.markdown(summary)

            if url:
                st.markdown(f"[Read original article]({url})")

else:
    st.info(
        "Click the button above to fetch and generate your latest five summaries."
    )
