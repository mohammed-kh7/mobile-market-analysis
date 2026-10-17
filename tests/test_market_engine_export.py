import csv
import io
import unittest

import pandas as pd

import market_engine


class CsvReportTests(unittest.TestCase):
    def test_report_is_utf8_csv_and_external_text_cannot_become_a_formula(self):
        reviews = pd.DataFrame([
            {"app_title": "=1+1", "user_name": " @SUM(1,1)", "score": 1,
             "sentiment": "Negative", "review_at": pd.Timestamp("2026-10-14"),
             "thumbs_up": 2, "app_version": "  =2+2",
             "content": '\t=HYPERLINK("https://example.invalid")'},
            {"app_title": "تطبيق عربي", "user_name": "أحمد", "score": 5,
             "sentiment": "Positive", "review_at": pd.Timestamp("2026-10-15"),
             "thumbs_up": 1, "app_version": "1.0", "content": "ممتاز"},
        ])

        report = market_engine.build_csv_report(reviews)
        self.assertTrue(report.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.DictReader(io.StringIO(report.decode("utf-8-sig"))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(list(rows[0]), list(market_engine.CSV_COLUMNS))
        self.assertEqual(rows[0]["app_title"], "'=1+1")
        self.assertEqual(rows[0]["user_name"], "' @SUM(1,1)")
        self.assertEqual(rows[0]["app_version"], "'  =2+2")
        self.assertEqual(rows[0]["content"], '\'\t=HYPERLINK("https://example.invalid")')
        self.assertEqual(rows[1]["content"], "ممتاز")


if __name__ == "__main__":
    unittest.main()
