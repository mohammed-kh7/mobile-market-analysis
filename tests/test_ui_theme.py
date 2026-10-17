import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import market_engine
from ui_theme import APP_COLORS, PALETTES, SENTIMENT_COLORS, STAR_COLORS
from streamlit.testing.v1 import AppTest


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(first, second):
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class ThemeContrastTests(unittest.TestCase):
    def test_body_and_muted_text_meet_wcag_aa_in_both_modes(self):
        for mode, palette in PALETTES.items():
            with self.subTest(mode=mode):
                for text_token in ("text", "muted", "muted_2"):
                    self.assertGreaterEqual(
                        contrast_ratio(palette[text_token], palette["surface"]),
                        4.5,
                        f"{text_token} contrast fails in {mode} mode",
                    )

    def test_primary_button_label_meets_wcag_aa_in_both_modes(self):
        for mode, palette in PALETTES.items():
            with self.subTest(mode=mode):
                self.assertGreaterEqual(
                    contrast_ratio(palette["on_primary"], palette["blue"]),
                    4.5,
                )
                self.assertGreaterEqual(
                    contrast_ratio(palette["on_primary"], palette["button_hover"]),
                    4.5,
                )

    def test_sentiment_text_meets_wcag_aa_in_both_modes(self):
        for mode, colors in SENTIMENT_COLORS.items():
            with self.subTest(mode=mode):
                for sentiment, color in colors.items():
                    self.assertGreaterEqual(
                        contrast_ratio(color, PALETTES[mode]["surface"]),
                        4.5,
                        f"{sentiment} text contrast fails in {mode} mode",
                    )

    def test_app_chart_colors_follow_the_teal_and_green_theme(self):
        for mode, colors in APP_COLORS.items():
            with self.subTest(mode=mode):
                self.assertEqual(len(colors), len(set(colors)))
                self.assertIn(PALETTES[mode]["green"], colors)
                self.assertNotIn(PALETTES[mode]["amber"], colors)
                for color in colors:
                    self.assertGreaterEqual(
                        contrast_ratio(color, PALETTES[mode]["surface"]),
                        3.0,
                        f"Chart color {color} lacks contrast in {mode} mode",
                    )

    def test_star_rating_palette_has_three_distinct_high_contrast_colors(self):
        for mode, colors in STAR_COLORS.items():
            with self.subTest(mode=mode):
                self.assertEqual(len(colors), 3)
                self.assertEqual(len(set(colors)), 3)
                for color in colors:
                    self.assertGreaterEqual(
                        contrast_ratio(color, PALETTES[mode]["surface"]), 3.0,
                    )

    def test_theme_switch_updates_session_state_across_reruns(self):
        reviews = pd.DataFrame(
            [
                {
                    "review_id": f"review-{index}",
                    "app_id": "com.example.fit" if index < 4 else "com.example.run",
                    "app_title": "Fit App" if index < 4 else "Run App",
                    "user_name": f"Reviewer {index}",
                    "score": index % 5 + 1,
                    "content": f"Training feedback {index}",
                    "review_at": pd.Timestamp("2026-10-14") - pd.Timedelta(days=index),
                    "thumbs_up": index,
                    "app_version": "1.0",
                    "sentiment": ("Negative", "Neutral", "Positive")[index % 3],
                }
                for index in range(8)
            ]
        )
        analyzed_apps = [
            {"appId": "com.example.fit", "title": "Fit App", "developer": "Fit Co",
             "score": 4.2, "icon": ""},
            {"appId": "com.example.run", "title": "Run App", "developer": "Run Co",
             "score": 4.4, "icon": ""},
        ]
        app = AppTest.from_file(
            str(Path(__file__).parents[1] / "app.py"),
            default_timeout=10,
        )
        app.session_state["analyzed"] = analyzed_apps

        with patch.object(market_engine, "load_reviews", return_value=reviews):
            app.run()
        self.assertFalse(app.exception)
        styles = "\n".join(element.value for element in app.markdown)
        self.assertIn(
            '[data-testid="stAppViewContainer"] { direction: rtl; }',
            styles,
        )
        self.assertIn(
            '[data-testid="stMain"], [data-testid="stSidebar"] { direction: rtl; }',
            styles,
        )
        self.assertIn(
            '[data-testid="stSidebar"][aria-expanded="false"] {\n'
            '  visibility: hidden;\n'
            '  overflow: hidden;\n'
            '}',
            styles,
        )
        self.assertNotIn(".stApp { direction: rtl; }", styles)
        comparison_grid = next(
            element.value
            for element in app.markdown
            if 'aria-label="بطاقات المراجعات"' in element.value
        )
        self.assertEqual(comparison_grid.count('class="review-card"'), 8)

        with patch.object(market_engine, "load_reviews", return_value=reviews):
            app.toggle(key="theme_light").set_value(True).run()
        self.assertEqual(app.session_state["theme"], "light")
        self.assertFalse(app.exception)

        with patch.object(market_engine, "load_reviews", return_value=reviews):
            app.toggle(key="theme_light").set_value(False).run()
        self.assertEqual(app.session_state["theme"], "dark")
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
