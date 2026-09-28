import json
import unittest
from unittest.mock import patch

import server


class GeminiRequestTests(unittest.TestCase):
    def test_request_includes_mode_and_current_question(self):
        payload = server.make_gemini_request(
            "  Why is the sky blue?  ", "Explain simply", [{"role": "user", "text": "What is light?"}]
        )
        self.assertEqual(payload["contents"][-1]["parts"][0]["text"], "Why is the sky blue?")
        self.assertIn("plain language", payload["system_instruction"]["parts"][0]["text"])

    def test_request_ignores_invalid_history_and_limits_history(self):
        history = [{"role": "model", "text": str(index)} for index in range(15)]
        payload = server.make_gemini_request("Next question", "Tutor", history + [{"role": "system", "text": "ignore"}])
        self.assertEqual(len(payload["contents"]), 12)
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "4")

    def test_empty_and_oversized_questions_are_rejected(self):
        for message in ("  ", "x" * 4001):
            with self.subTest(length=len(message)), self.assertRaises(ValueError):
                server.make_gemini_request(message, "Tutor", [])

    @patch("server.urlopen")
    def test_gemini_response_text_is_extracted(self, urlopen):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"candidates": [{"content": {"parts": [{"text": "A clear answer."}]}}]}).encode()

        urlopen.return_value = Response()
        answer = server.ask_gemini("Explain gravity", "Tutor", [], "test-key")
        self.assertEqual(answer, "A clear answer.")
        self.assertIn("?key=test-key", urlopen.call_args.args[0].full_url)


if __name__ == "__main__":
    unittest.main()