#!/usr/bin/env python3
"""Ensure the one headed Chrome owner used by every Consult invocation."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

from consult_runtime import CDP_PORT, browser_agent_home


ENSURE_TIMEOUT_SECONDS = 10


def endpoint_ready() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=1):
            return True
    except Exception:
        return False


def endpoint_uses_profile(profile: Path) -> bool:
    try:
        listener = subprocess.run(
            ["/usr/sbin/lsof", f"-tiTCP:{CDP_PORT}", "-sTCP:LISTEN"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()[0]
        command = subprocess.run(
            ["/bin/ps", "-p", listener, "-o", "command="],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (IndexError, OSError, subprocess.CalledProcessError):
        return False
    return (
        f"--remote-debugging-port={CDP_PORT}" in command
        and f"--user-data-dir={profile.resolve()}" in command
    )


def main(argv: list[str]) -> int:
    if argv != ["--ensure"]:
        print(f"usage: {Path(sys.argv[0]).name} --ensure", file=sys.stderr)
        return 2
    home = browser_agent_home()
    profile = home / "browser-profile"
    if endpoint_ready():
        if endpoint_uses_profile(profile):
            return 0
        print(
            f"CDP port {CDP_PORT} is owned by a different Chrome profile; "
            f"expected {profile}",
            file=sys.stderr,
        )
        return 1

    chrome = Path(
        os.environ.get(
            "CONSULT_CHROME_BIN",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
    ).expanduser()
    if not chrome.is_file():
        print(f"Google Chrome not found: {chrome}", file=sys.stderr)
        return 1

    profile.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.gettempdir())
    lock_path = temp / f"consult-chrome-{os.getuid()}-{CDP_PORT}.lock"
    log_path = temp / f"consult-chrome-{os.getuid()}-{CDP_PORT}.log"

    with lock_path.open("a+") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if endpoint_ready():
            if endpoint_uses_profile(profile):
                return 0
            print(
                f"CDP port {CDP_PORT} became ready with an unexpected profile; expected {profile}",
                file=sys.stderr,
            )
            return 1
        with log_path.open("ab") as log_handle:
            subprocess.Popen(
                [
                    str(chrome),
                    "--remote-debugging-address=127.0.0.1",
                    f"--remote-debugging-port={CDP_PORT}",
                    f"--user-data-dir={profile}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--no-startup-window",
                ],
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
        deadline = time.monotonic() + ENSURE_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if endpoint_ready() and endpoint_uses_profile(profile):
                return 0
            time.sleep(0.05)

    print(
        f"Chrome debugging endpoint did not become ready at http://127.0.0.1:{CDP_PORT}; "
        f"see {log_path}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
