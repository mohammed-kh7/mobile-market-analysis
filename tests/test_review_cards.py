import unittest
from datetime import datetime

import pandas as pd

from review_cards import build_review_card, filter_reviews
from streamlit.testing.v1 import AppTest


class ReviewCardTests(unittest.TestCase):
    def test_card_includes_review_identity_score_date_and_comment(self):
        card = build_review_card(
            {
                "review_id": "review-1",
                "user_name": "Sam",
                "score": 4,
                "content": "Great training plans",
                "review_at": datetime(2026, 10, 14, 9, 30),
                "sentiment": "Positive",
                "thumbs_up": 3,
            },
            language="en",
            app_title="Fit App",
        )

        self.assertIn('class="review-card"', card)
        self.assertIn("Sam", card)
        self.assertIn("Great training plans", card)
        self.assertIn("4/5", card)
        self.assertIn("aria-valuenow=\"4\"", card)
        self.assertIn("--rating-position:75.00%", card)
        self.assertIn("2026-10-14", card)
        self.assertIn("Fit App", card)

    def test_card_escapes_untrusted_review_content(self):
        card = build_review_card(
            {
                "review_id": "review-2",
                "user_name": "<img src=x onerror=alert(1)>",
                "score": 2,
                "content": "<script>alert(1)</script>",
                "review_at": datetime(2026, 10, 14),
                "sentiment": "Negative",
                "thumbs_up": 0,
            },
            language="en",
        )

        self.assertNotIn("<script>", card)
        self.assertNotIn("<img", card)
        self.assertIn("&lt;script&gt;", card)
        self.assertIn("&lt;img", card)

    def test_missing_reviewer_name_uses_localized_fallback(self):
        card = build_review_card(
            {
                "review_id": "review-3",
                "user_name": "",
                "score": 5,
                "content": "Excellent",
                "review_at": datetime(2026, 10, 14),
                "sentiment": "Positive",
                "thumbs_up": 0,
            },
            language="ar",
        )

        self.assertIn("مراجع", card)
        self.assertIn('dir="rtl"', card)
        self.assertIn('aria-valuetext="5 من 5"', card)

    def test_rating_and_sentiment_filters_compose(self):
        reviews = pd.DataFrame(
            [
                {"review_id": "low", "score": 2, "sentiment": "Negative"},
                {"review_id": "high-negative", "score": 4, "sentiment": "Negative"},
                {"review_id": "high-positive", "score": 5, "sentiment": "Positive"},
            ]
        )

        filtered = filter_reviews(reviews, rating_range=(3, 5), sentiment="Negative")

        self.assertEqual(filtered["review_id"].tolist(), ["high-negative"])

    def test_rating_filter_rejects_out_of_range_values(self):
        with self.assertRaises(ValueError):
            filter_reviews(pd.DataFrame(), rating_range=(0, 8), sentiment="all")

    def test_component_renders_all_cards_and_filters_them_by_slider(self):
        script = """
import pandas as pd
import streamlit as st
from review_cards import render_review_cards
import ui_theme

ui_theme.apply_theme("dark")

def translate(key):
    return {
        "box_all": "All",
        "box_filter_sent": "Sentiment",
        "box_filter_stars": "Rating range",
        "box_empty": "No matching reviews",
        "box_showing": "{n} reviews",
        "box_section": "Reviews",
    }[key]

reviews = pd.DataFrame([
    {"review_id": str(i), "user_name": f"Reviewer {i}", "score": score,
     "content": f"Feedback {i}", "review_at": pd.Timestamp("2026-10-14"),
     "sentiment": "Positive", "thumbs_up": 0}
    for i, score in enumerate([1, 2, 3, 4, 5, 4, 2, 5])
])
render_review_cards(
    reviews, key="test", language="en", translate=translate,
    sentiment_label=lambda value: value,
)
"""
        app = AppTest.from_string(script).run()
        self.assertFalse(app.exception)
        grid = next(element.value for element in app.markdown if 'class="review-grid"' in element.value)
        self.assertEqual(grid.count('class="review-card"'), 8)

        app.slider(key="review_rating_range_test").set_value((4, 5)).run()
        self.assertFalse(app.exception)
        filtered_grid = next(
            element.value for element in app.markdown if 'class="review-grid"' in element.value
        )
        self.assertEqual(filtered_grid.count('class="review-card"'), 4)


if __name__ == "__main__":
    unittest.main()
