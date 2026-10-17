import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import market_engine as engine


class AppWorkflowTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=30)

    def test_language_and_theme_can_switch_in_all_combinations(self):
        app = self.app().run()
        self.assertFalse(app.exception)
        for language in ("en", "ar"):
            app.button(key="lang_switch").click().run()
            self.assertEqual(app.session_state["lang"], language)
            for light in (True, False):
                app.toggle(key="theme_light").set_value(light).run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["theme"], "light" if light else "dark")

    def test_selection_limits_and_analysis_use_streamed_batches(self):
        apps = [{"appId": f"com.app{i}", "title": f"App {i}", "developer": "Developer",
                 "score": 4.2, "icon": ""} for i in range(5)]
        app = self.app()
        app.session_state["results"] = apps
        app.run()
        selection = [button for button in app.button if button.key and button.key.startswith("sel_")]
        selection[0].click().run()
        run = app.button(key="run_analysis")
        self.assertTrue(run.disabled)
        for index in range(1, 4):
            [button for button in app.button if button.key and button.key.startswith("sel_")][index].click().run()
        self.assertEqual(len(app.session_state["selected_apps"]), 4)
        last = [button for button in app.button if button.key and button.key.startswith("sel_")][-1]
        self.assertTrue(last.disabled)
        with patch.object(engine, "iter_review_batches", return_value=iter([])) as stream, \
             patch.object(engine, "save_app"):
            app.button(key="run_analysis").click().run()
        self.assertEqual(stream.call_count, 4)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.error), 4)


if __name__ == "__main__":
    unittest.main()
