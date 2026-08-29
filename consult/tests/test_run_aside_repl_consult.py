from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_aside_repl_consult.py"
)
SPEC = importlib.util.spec_from_file_location("run_aside_repl_consult_test", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AsideReplConsultTest(unittest.TestCase):
    def test_quality_flag_is_required_and_limited(self) -> None:
        with self.assertRaises(SystemExit):
            MODULE.parse_args([])
        self.assertEqual(MODULE.parse_args(["--quality", "xhigh", "--packet", "p"]).quality, "xhigh")
        self.assertEqual(MODULE.parse_args(["--quality", "pro", "--packet", "p"]).quality, "pro")
        with self.assertRaises(SystemExit):
            MODULE.parse_args(["--quality", "high", "--packet", "p"])

    def test_work_project_url_is_fail_closed(self) -> None:
        self.assertTrue(
            MODULE.is_work_project_url(
                "https://chatgpt.com/g/g-p-test-work/project"
            )
        )
        self.assertFalse(MODULE.is_work_project_url("https://chatgpt.com/"))
        self.assertFalse(
            MODULE.is_work_project_url(
                "https://chatgpt.com/g/g-p-test-work/c/conversation"
            )
        )

    def test_generated_script_has_quality_mapping_and_hard_deadline(self) -> None:
        xhigh = MODULE.build_repl_script(
            project_url="https://chatgpt.com/g/g-p-test-work/project",
            quality="xhigh",
            packet="receipt\npacket",
            receipt="receipt",
            response_timeout_ms=1000,
        )
        pro = MODULE.build_repl_script(
            project_url="https://chatgpt.com/g/g-p-test-work/project",
            quality="pro",
            packet="receipt\npacket",
            receipt="receipt",
            response_timeout_ms=1000,
        )

        self.assertEqual(MODULE.SUBMIT_TIMEOUT_SECONDS, 120)
        self.assertIn("var targetIndex = 4", xhigh)
        self.assertIn("var targetIndex = 5", pro)
        self.assertIn("pre-submit preparation exceeded 110 seconds", pro)
        self.assertIn("user turn committed after 120-second deadline", pro)
        self.assertIn("submitElapsedMs >= 120000", pro)
        self.assertIn("Promise.race", pro)
        self.assertIn("pre-submit preparation exceeded 110 seconds", pro)
        self.assertIn("ASIDE_REPL_SUBMIT_UNKNOWN", pro)
        self.assertIn("ASIDE_REPL_SUBMIT_RESULT", pro)
        self.assertIn("ASIDE_REPL_RESPONSE_RESULT", pro)

    def test_streaming_runner_parses_both_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "aside"
            fake.write_text(
                """#!/usr/bin/env python3
print('ASIDE_REPL_SUBMIT_RESULT {"quality":"pro","submitElapsedMs":1234,"conversationUrl":"https://chatgpt.com/g/g-p-test-work/c/1"}')
print('ASIDE_REPL_RESPONSE_RESULT {"responseText":"receipt\\\\nanswer","responseElapsedMs":5678,"conversationUrl":"https://chatgpt.com/g/g-p-test-work/c/1"}')
""",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            path = f"{temp}{os.pathsep}{os.environ.get('PATH', '')}"
            with mock.patch.dict(os.environ, {"PATH": path}):
                submitted, response, submit_s, response_s, transcript = (
                    MODULE.run_repl_streaming(
                        "ignored",
                        submit_timeout=1,
                        response_timeout=1,
                    )
                )

        self.assertEqual(submitted["quality"], "pro")
        self.assertEqual(response["responseText"], "receipt\nanswer")
        self.assertEqual(submit_s, 1.234)
        self.assertEqual(response_s, 5.678)
        self.assertIn("ASIDE_REPL_SUBMIT_RESULT", transcript)

    def test_streaming_runner_rejects_missing_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "aside"
            fake.write_text("#!/bin/sh\nprintf 'no markers\\n'\n", encoding="utf-8")
            fake.chmod(0o755)
            path = f"{temp}{os.pathsep}{os.environ.get('PATH', '')}"
            with mock.patch.dict(os.environ, {"PATH": path}):
                with self.assertRaisesRegex(RuntimeError, "before submission marker"):
                    MODULE.run_repl_streaming(
                        "ignored",
                        submit_timeout=1,
                        response_timeout=1,
                    )

    def test_streaming_runner_classifies_submit_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "aside"
            fake.write_text(
                """#!/usr/bin/env python3
print('ASIDE_REPL_SUBMIT_UNKNOWN {"quality":"pro","reason":"commit unverified"}')
""",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            path = f"{temp}{os.pathsep}{os.environ.get('PATH', '')}"
            with mock.patch.dict(os.environ, {"PATH": path}):
                with self.assertRaisesRegex(
                    MODULE.SubmitUnknownError, "do not retry"
                ):
                    MODULE.run_repl_streaming(
                        "ignored",
                        submit_timeout=1,
                        response_timeout=1,
                    )

    def test_main_returns_76_for_submit_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "aside"
            fake.write_text(
                """#!/usr/bin/env python3
print('ASIDE_REPL_SUBMIT_UNKNOWN {"quality":"pro","reason":"commit unverified"}')
""",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            packet = root / "packet.md"
            packet.write_text("question", encoding="utf-8")
            path = f"{temp}{os.pathsep}{os.environ.get('PATH', '')}"
            with mock.patch.dict(os.environ, {"PATH": path}):
                result = MODULE.main(
                    [
                        "--quality", "pro",
                        "--packet", str(packet),
                        "--url", "https://chatgpt.com/g/g-p-test-work/project",
                        "--response-output", str(root / "response.md"),
                        "--json-output", str(root / "result.json"),
                        "--stderr-output", str(root / "stderr.log"),
                    ]
                )

            self.assertEqual(result, 76)
            self.assertIn(
                "do not retry",
                (root / "stderr.log").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
