from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


class ConsultAsideContractTest(unittest.TestCase):
    def test_main_skill_uses_aside_without_legacy_browser_helpers(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("aside exec", skill)
        self.assertIn("chatgpt-work-consult", skill)
        self.assertIn("SURFACE` is `Work", skill)
        self.assertNotIn("run_agbrowse", skill)
        self.assertNotIn("ensure_consult_chrome", skill)

    def test_inner_skill_fails_closed_outside_work(self) -> None:
        skill = (
            ROOT / "aside-skill" / "chatgpt-work-consult" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Never use temporary chat", skill)
        self.assertIn("Never submit from global Chat", skill)
        self.assertIn("GPT-5.6 Sol", skill)
        self.assertIn("매우 높음", skill)
        self.assertIn("ASIDE_WORK_CONSULT_ERROR", skill)

    def test_playwright_fallback_is_hidden_not_main_content(self) -> None:
        fallback = ROOT / "fallback" / "consult-playwright"
        if fallback.is_symlink():
            self.assertEqual(
                fallback.resolve(), (REPO / "consult-playwright").resolve()
            )
        else:
            # Rubato's bundle dereferences the canonical hidden link so the
            # fallback survives distribution without becoming a top-level skill.
            self.assertTrue(fallback.is_dir())
        self.assertTrue((fallback / "SKILL.md").is_file())
        self.assertFalse((ROOT / "scripts" / "run_agbrowse_consult.py").exists())


if __name__ == "__main__":
    unittest.main()
