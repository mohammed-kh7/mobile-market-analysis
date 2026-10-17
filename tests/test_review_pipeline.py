import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import market_engine as engine


def reviews(start, count):
    return [{"reviewId": str(i), "score": 4, "content": "Useful app"}
            for i in range(start, start + count)]


class ReviewPipelineTests(unittest.TestCase):
    def test_requests_and_parsing_are_bounded_at_500(self):
        with patch.object(engine, "gp_reviews", side_effect=[
            (reviews(0, 500), "next"), (reviews(500, 500), "last"),
            (reviews(1000, 120), None),
        ]) as upstream:
            batches = list(engine.iter_review_batches("app", 1500))
        self.assertEqual([len(batch) for batch in batches], [500, 500, 120])
        self.assertTrue(all(call.kwargs["count"] == 500 for call in upstream.call_args_list))
        self.assertEqual(len(engine.reviews_to_frame(batches[0], "app")), 500)

    def test_duplicate_pages_stop_without_looping(self):
        with patch.object(engine, "gp_reviews", return_value=(reviews(0, 500), "next")) as upstream:
            batches = list(engine.iter_review_batches("app", 1000))
        self.assertEqual(len(batches), 1)
        self.assertEqual(upstream.call_count, 2)

    def test_failure_after_first_page_is_reported(self):
        with patch.object(engine, "gp_reviews", side_effect=[
            (reviews(0, 500), "next"), RuntimeError("offline"),
            RuntimeError("offline"), RuntimeError("offline"),
        ]), patch.object(engine.time, "sleep"):
            batches = engine.iter_review_batches("app", 1000)
            self.assertEqual(len(next(batches)), 500)
            with self.assertRaises(RuntimeError):
                next(batches)

    def test_refresh_app_preserves_existing_reviews(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "reviews.db")
            app = {"appId": "app", "title": "Title", "developer": "Dev", "score": 4, "icon": ""}
            engine.save_app(app, database)
            engine.save_reviews(engine.reviews_to_frame(reviews(0, 2), "app"), database)
            engine.save_app({**app, "title": "Updated"}, database)
            self.assertEqual(len(engine.load_reviews(["app"], database)), 2)


if __name__ == "__main__":
    unittest.main()
