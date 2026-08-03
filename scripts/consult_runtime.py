"""Single-browser runtime contract shared by Consult helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


CDP_PORT = "9222"
DEFAULT_BROWSER_AGENT_HOME = Path.home() / ".codex" / "browser-profiles" / "consult-agbrowse"
DEFAULT_CHROME_LAUNCHER = Path(__file__).with_name("ensure_consult_chrome.py")


def browser_agent_home(source: Mapping[str, str] | None = None) -> Path:
    values = source if source is not None else os.environ
    configured = values.get("CONSULT_BROWSER_AGENT_HOME")
    return Path(configured).expanduser() if configured else DEFAULT_BROWSER_AGENT_HOME


def chrome_launcher(source: Mapping[str, str] | None = None) -> Path:
    values = source if source is not None else os.environ
    configured = values.get("CONSULT_CHROME_LAUNCHER")
    return Path(configured).expanduser() if configured else DEFAULT_CHROME_LAUNCHER


def browser_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(source if source is not None else os.environ)
    env["BROWSER_AGENT_HOME"] = str(browser_agent_home(env))
    env["CDP_PORT"] = CDP_PORT
    env["AGBROWSE_WEB_AI_AUTO_START"] = "0"
    env.setdefault("AGBROWSE_HEAVY_SITE_COMPAT", "1")
    return env
