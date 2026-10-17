from __future__ import annotations

import html
import math
from datetime import date, datetime
from math import isfinite
from typing import Callable, Mapping

import pandas as pd
import streamlit as st


def _format_date(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except (TypeError, ValueError):
        return "—"


def build_review_card(
    review: Mapping[str, object],
    *,
    language: str,
    app_title: str | None = None,
) -> str:
    name = str(review.get("user_name") or "").strip()
    labels = {
        "ar": {
            "reviewer": "مراجع",
            "positive": "إيجابي",
            "neutral": "محايد",
            "negative": "سلبي",
            "rating": "التقييم",
            "likes": "إعجاب",
        },
        "en": {
            "reviewer": "Reviewer",
            "positive": "Positive",
            "neutral": "Neutral",
            "negative": "Negative",
            "rating": "Rating",
            "likes": "likes",
        },
    }
    copy = labels["ar" if language == "ar" else "en"]
    name = name or copy["reviewer"]
    try:
        score = float(review.get("score") or 1)
    except (TypeError, ValueError):
        score = 1.0
    if not isfinite(score):
        score = 1.0
    score = min(5.0, max(1.0, score))
    score_text = f"{score:g}"
    position = (score - 1) / 4 * 100
    rating_value_text = f"{score_text} من 5" if language == "ar" else f"{score_text} out of 5"
    sentiment = str(review.get("sentiment") or "Neutral").lower()
    if sentiment not in {"positive", "neutral", "negative"}:
        sentiment = "neutral"
    content = html.escape(str(review.get("content") or "").strip())
    app = app_title if app_title is not None else str(review.get("app_title") or "")
    date_text = _format_date(review.get("review_at"))
    try:
        likes = max(0, int(review.get("thumbs_up") or 0))
    except (TypeError, ValueError):
        likes = 0
    direction = "rtl" if language == "ar" else "ltr"

    return (
        f'<article class="review-card" data-sentiment="{sentiment}" dir="{direction}">'
        '<header class="review-card-header">'
        '<div class="review-person">'
        f'<span class="review-avatar" aria-hidden="true">{html.escape(name[:1])}</span>'
        f'<strong class="review-name">{html.escape(name)}</strong>'
        "</div>"
        f'<time class="review-date" datetime="{html.escape(date_text)}">{html.escape(date_text)}</time>'
        "</header>"
        f'<p class="review-copy" title="{content}">{content}</p>'
        '<footer class="review-card-footer">'
        f'<div class="review-rating" role="meter" aria-valuemin="1" aria-valuemax="5" '
        f'aria-valuenow="{score_text}" aria-valuetext="{rating_value_text}" '
        f'aria-label="{copy["rating"]} {score_text} out of 5">'
        f'<span class="review-rating-value">{score_text}/5</span>'
        f'<span class="review-rating-track"><span style="--rating-position:{position:.2f}%"></span></span>'
        "</div>"
        f'<span class="review-sentiment {sentiment}">{copy[sentiment]}</span>'
        f'<span class="review-likes">{likes} {copy["likes"]}</span>'
        f'<span class="review-app">{html.escape(str(app))}</span>'
        "</footer>"
        "</article>"
    )


def filter_reviews(
    reviews: pd.DataFrame,
    *,
    rating_range: tuple[int, int],
    sentiment: str,
) -> pd.DataFrame:
    if (
        not isinstance(rating_range, tuple)
        or len(rating_range) != 2
        or any(type(rating) is not int or not 1 <= rating <= 5 for rating in rating_range)
        or rating_range[0] > rating_range[1]
    ):
        raise ValueError("Rating range must be an ordered pair between 1 and 5.")
    if sentiment not in {"all", "Positive", "Neutral", "Negative"}:
        raise ValueError("Sentiment filter is invalid.")

    filtered = reviews[reviews["score"].between(*rating_range)]
    if sentiment != "all":
        filtered = filtered[filtered["sentiment"] == sentiment]
    return filtered


def render_review_cards(
    reviews,
    *,
    key: str,
    language: str,
    translate: Callable[[str], str],
    sentiment_label: Callable[[str], str],
    app_title: str | None = None,
) -> None:
    sentiment_options = ("all", "Positive", "Neutral", "Negative")
    sentiment_labels = {
        "all": translate("box_all"),
        "Positive": sentiment_label("Positive"),
        "Neutral": sentiment_label("Neutral"),
        "Negative": sentiment_label("Negative"),
    }

    sentiment_col, rating_col = st.columns([1.2, 1.8])
    selected_sentiment = sentiment_col.selectbox(
        translate("box_filter_sent"),
        sentiment_options,
        format_func=lambda value: sentiment_labels[value],
        index=0,
        key=f"review_sentiment_{key}",
    ) or "all"
    rating_range = rating_col.slider(
        translate("box_filter_stars"),
        min_value=1,
        max_value=5,
        value=(1, 5),
        step=1,
        key=f"review_rating_range_{key}",
    )
    low_rating, high_rating = rating_range
    filtered = filter_reviews(
        reviews,
        rating_range=(low_rating, high_rating),
        sentiment=selected_sentiment,
    )

    low_percent = (low_rating - 1) / 4 * 100
    selected_percent = (high_rating - low_rating) / 4 * 100
    st.markdown(
        '<div class="rating-range-track" aria-hidden="true">'
        f'<span style="--range-start:{low_percent:.2f}%;--range-width:{selected_percent:.2f}%"></span>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"{low_rating}/5 – {high_rating}/5")

    total = len(filtered)
    if total == 0:
        st.info(translate("box_empty"))
        return

    ordered = filtered.sort_values("review_at", ascending=False)
    page_size = 60
    pages = max(1, math.ceil(total / page_size))
    page_key = f"review_page_{key}"
    st.session_state[page_key] = min(st.session_state.get(page_key, 1), pages)
    page = st.number_input(
        "صفحة المراجعات" if language == "ar" else "Review page",
        min_value=1, max_value=pages, step=1, key=page_key,
    )
    ordered = ordered.iloc[(page - 1) * page_size:page * page_size]
    cards = "".join(
        build_review_card(row, language=language, app_title=app_title)
        for row in ordered.to_dict(orient="records")
    )
    st.markdown(
        f'<div class="review-grid" role="region" tabindex="0" '
        f'aria-label="{html.escape(translate("box_section"))}">{cards}</div>',
        unsafe_allow_html=True,
    )
    st.caption(translate("box_showing").format(n=total))
    st.caption(f"{page} / {pages}")
