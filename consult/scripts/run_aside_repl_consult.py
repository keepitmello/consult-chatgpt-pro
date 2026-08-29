#!/usr/bin/env python3
"""Submit and recover a ChatGPT Work consult through deterministic Aside REPL calls."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import selectors
import secrets
import shutil
import subprocess
import sys
import time
from typing import Any, Sequence
from urllib.parse import urlparse


SUBMIT_TIMEOUT_SECONDS = 120
DEFAULT_RESPONSE_TIMEOUT_SECONDS = 3600
DEFAULT_CONFIG = Path.home() / ".codex" / "consult.env"
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SUBMIT_MARKER = "ASIDE_REPL_SUBMIT_RESULT "
SUBMIT_UNKNOWN_MARKER = "ASIDE_REPL_SUBMIT_UNKNOWN "
RESPONSE_MARKER = "ASIDE_REPL_RESPONSE_RESULT "


class SubmitUnknownError(RuntimeError):
    """The send click happened but provider commit could not be proven."""


def read_config_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() != key:
            continue
        value = value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')):
            value = value[1:-1]
        return value or None
    return None


def is_work_project_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "chatgpt.com"
        and parsed.path.startswith("/g/g-p-")
        and "-work/" in parsed.path
        and parsed.path.endswith("/project")
    )


def js(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_repl_script(
    *,
    project_url: str,
    quality: str,
    packet: str,
    receipt: str,
    response_timeout_ms: int,
) -> str:
    target_index = 4 if quality == "xhigh" else 5
    target_label = "매우 높음" if quality == "xhigh" else "Pro"
    return f"""
var projectUrl = {js(project_url)};
var quality = {js(quality)};
var packet = {js(packet)};
var targetIndex = {target_index};
var targetLabel = {js(target_label)};
var submitStartedAt = Date.now();
var submitStage = 'open-isolated-tab';
var submitState = await Promise.race([
  (async () => {{
    var tabsBeforeOpen = await listBrowserTabs();
    var idsBeforeOpen = new Set(tabsBeforeOpen.map((tab) => tab.targetId));
    var workPage = await openTab('about:blank');
    var openedTabs = await listBrowserTabs();
    var ownedTab = openedTabs.find((tab) => !idsBeforeOpen.has(tab.targetId));
    if (!ownedTab) throw new Error('isolated consult tab not found');
    submitStage = 'load-work-project';
    await workPage.goto(projectUrl);
    await workPage.waitForLoadState('domcontentloaded');
    await snapshot(workPage, {{ interactive: true }});
    submitStage = 'wait-work-composer';
    var composer = workPage.getByRole('textbox', {{ name: 'Work에서 새 채팅' }});
    await composer.waitFor({{ state: 'visible', timeout: 20000 }});
    var assistantCountBefore = await workPage.locator('[data-message-author-role="assistant"]').count();
    if (assistantCountBefore !== 0) throw new Error('isolated Work composer contains stale assistant turns');
    submitStage = 'select-tier';
    var tierButton = workPage.getByRole('button', {{ name: /^(추론 수준|매우 높음|Pro)$/ }}).last();
    await tierButton.click();
    var performance = workPage.getByRole('menuitem', {{ name: '성능' }});
    await performance.waitFor({{ state: 'visible', timeout: 5000 }});
    var tierSnapshot = await snapshot(workPage, {{ interactive: true }});
    var positionMatch = tierSnapshot.tree.match(/5개 중 ([1-5])번째/);
    if (!positionMatch) throw new Error('tier position not readable');
    var currentIndex = Number(positionMatch[1]);
    performance = workPage.getByRole('menuitem', {{ name: '성능' }});
    await performance.focus();
    var direction = targetIndex > currentIndex ? 'ArrowRight' : 'ArrowLeft';
    for (var i = 0; i < Math.abs(targetIndex - currentIndex); i += 1) {{
      await workPage.keyboard.press(direction);
    }}
    var selectedSnapshot = await snapshot(workPage, {{ interactive: true }});
    if (!selectedSnapshot.tree.includes(targetLabel + ', 5개 중 ' + targetIndex + '번째')) throw new Error('requested tier not verified');
    submitStage = 'verify-model';
    await workPage.getByRole('menuitem', {{ name: '모델 선택' }}).click();
    var sol = workPage.getByRole('menuitemradio', {{ name: 'GPT-5.6 Sol' }});
    await sol.waitFor({{ state: 'visible', timeout: 5000 }});
    if ((await sol.getAttribute('aria-checked')) !== 'true') throw new Error('GPT-5.6 Sol not checked');
    await workPage.keyboard.press('Escape');
    submitStage = 'fill-composer';
    await composer.click();
    await workPage.keyboard.press('Meta+A');
    await workPage.keyboard.press('Backspace');
    await workPage.keyboard.insertText(packet);
    var canonical = await composer.evaluate((el) => Array.from(el.children).map((child) => child.textContent || '').join('\\n'));
    if (canonical !== packet) {{
      await composer.click();
      await workPage.keyboard.press('Meta+A');
      await workPage.keyboard.press('Backspace');
      await workPage.keyboard.insertText(packet);
      canonical = await composer.evaluate((el) => Array.from(el.children).map((child) => child.textContent || '').join('\\n'));
    }}
    if (canonical !== packet) throw new Error('composer canonical text mismatch');
    submitStage = 'ready-to-send';
    var send = workPage.getByRole('button', {{ name: '프롬프트 보내기' }});
    await send.waitFor({{ state: 'visible', timeout: 5000 }});
    return {{ workPage, ownedTargetId: ownedTab.targetId, send }};
  }})(),
  new Promise((_, reject) => setTimeout(
    () => reject(new Error('pre-submit preparation exceeded 110 seconds at ' + submitStage)),
    110000
  ))
]);
var workPage = submitState.workPage;
var remainingSubmitMs = 120000 - (Date.now() - submitStartedAt);
if (remainingSubmitMs <= 0) throw new Error('pre-submit preparation exceeded 120 seconds');
submitStage = 'commit-user-turn';
await submitState.send.click();
var userTurn = workPage.locator('[data-message-author-role="user"]').filter({{ hasText: {js(receipt)} }}).last();
try {{
  await userTurn.waitFor({{ state: 'visible', timeout: remainingSubmitMs }});
}} catch (error) {{
  console.log({js(SUBMIT_UNKNOWN_MARKER)} + JSON.stringify({{
    receipt: {js(receipt)},
    quality,
    reason: 'send clicked but user turn commit was not verified before deadline'
  }}));
  await workPage.close().catch(() => {{}});
  throw new Error('SUBMIT_UNKNOWN');
}}
var submitElapsedMs = Date.now() - submitStartedAt;
if (submitElapsedMs >= 120000) {{
  console.log({js(SUBMIT_UNKNOWN_MARKER)} + JSON.stringify({{
    receipt: {js(receipt)},
    quality,
    reason: 'user turn committed after 120-second deadline'
  }}));
  await workPage.close().catch(() => {{}});
  throw new Error('SUBMIT_UNKNOWN');
}}
var submittedTabs = await listBrowserTabs();
var submittedTab = submittedTabs.find((tab) => tab.targetId === submitState.ownedTargetId);
console.log({js(SUBMIT_MARKER)} + JSON.stringify({{
  ok: true,
  quality,
  model: 'GPT-5.6 Sol',
  tier: quality === 'xhigh' ? '매우 높음 (4 of 5)' : 'Pro (5 of 5)',
  submitElapsedMs,
  conversationUrl: submittedTab ? submittedTab.url : workPage.url()
}}));
var responseStartedAt = Date.now();
var assistantTurns = workPage.locator('[data-message-author-role="assistant"]');
var assistant = assistantTurns.nth(0);
await assistant.waitFor({{ state: 'visible', timeout: {response_timeout_ms} }});
var copyResponse = workPage.getByRole('button', {{ name: /^(응답 복사|Copy response)$/ }}).last();
await copyResponse.waitFor({{ state: 'visible', timeout: {response_timeout_ms} }});
var responseText = await assistant.innerText();
if (!responseText.includes({js(receipt)})) throw new Error('receipt missing from assistant response');
var completedTabs = await listBrowserTabs();
var completedTab = completedTabs.find((tab) => tab.targetId === submitState.ownedTargetId);
var finalConversationUrl = completedTab ? completedTab.url : workPage.url();
await workPage.close().catch(() => {{}});
console.log({js(RESPONSE_MARKER)} + JSON.stringify({{
  ok: true,
  responseText,
  responseElapsedMs: Date.now() - responseStartedAt,
  conversationUrl: finalConversationUrl
}}));
""".strip()


def run_repl_streaming(
    script: str,
    *,
    submit_timeout: int,
    response_timeout: int,
) -> tuple[dict[str, Any], dict[str, Any], float, float, str]:
    started = time.monotonic()
    process = subprocess.Popen(
        ["aside", "repl", script],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    transcript: list[str] = []
    submit_payload: dict[str, Any] | None = None
    submit_unknown_payload: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None
    submit_elapsed = 0.0
    # Aside CLI buffers REPL output until the JavaScript finishes, so Python
    # cannot observe the submit marker in real time. The in-JS Promise.race owns
    # the 120-second submit deadline; this is only a whole-process safety bound.
    process_deadline = started + submit_timeout + response_timeout
    response_deadline: float | None = None

    try:
        while response_payload is None:
            now = time.monotonic()
            deadline = process_deadline if submit_payload is None else response_deadline
            assert deadline is not None
            if now >= deadline:
                phase = "REPL process" if submit_payload is None else "response recovery"
                raise TimeoutError(f"Aside REPL {phase} timed out")
            events = selector.select(timeout=min(1.0, deadline - now))
            if not events:
                if process.poll() is not None:
                    break
                continue
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                continue
            transcript.append(line)
            clean = ANSI_RE.sub("", line).rstrip("\n")
            if clean.startswith(SUBMIT_MARKER):
                submit_payload = json.loads(clean[len(SUBMIT_MARKER):])
                submit_elapsed = float(submit_payload["submitElapsedMs"]) / 1000
                response_deadline = time.monotonic() + response_timeout
                print(
                    f"CONSULT_SUBMITTED quality={submit_payload['quality']} "
                    f"elapsed={submit_elapsed:.3f}s url={submit_payload['conversationUrl']}",
                    flush=True,
                )
            elif clean.startswith(SUBMIT_UNKNOWN_MARKER):
                submit_unknown_payload = json.loads(
                    clean[len(SUBMIT_UNKNOWN_MARKER):]
                )
            elif clean.startswith(RESPONSE_MARKER):
                response_payload = json.loads(clean[len(RESPONSE_MARKER):])
        process.wait(timeout=5)
    except BaseException:
        process.kill()
        process.wait()
        process.stdout.close()
        raise
    finally:
        selector.close()

    remaining = process.stdout.read()
    process.stdout.close()
    if remaining:
        transcript.append(remaining)
    if submit_unknown_payload is not None:
        raise SubmitUnknownError(
            "submission state unknown; do not retry\n"
            + json.dumps(submit_unknown_payload, ensure_ascii=False)
            + "\n"
            + "".join(transcript)
        )
    if submit_payload is None:
        raise RuntimeError(
            "Aside REPL exited before submission marker\n" + "".join(transcript)
        )
    if response_payload is None:
        raise RuntimeError(
            "Aside REPL exited before response marker\n" + "".join(transcript)
        )
    return (
        submit_payload,
        response_payload,
        submit_elapsed,
        float(response_payload["responseElapsedMs"]) / 1000,
        "".join(transcript),
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality", choices=("xhigh", "pro"), required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--url", default=None)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--response-output", default=".consult/consult-response.md")
    parser.add_argument("--json-output", default=".consult/aside-consult-response.json")
    parser.add_argument("--stderr-output", default=".consult/aside-consult-stderr.log")
    parser.add_argument("--response-timeout", type=int, default=DEFAULT_RESPONSE_TIMEOUT_SECONDS)
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    if not shutil.which("aside"):
        print("aside not found", file=sys.stderr)
        return 127
    project_url = (
        args.url
        or os.environ.get("CONSULT_CHATGPT_URL")
        or read_config_value(Path(args.config).expanduser(), "CONSULT_CHATGPT_URL")
    )
    if not is_work_project_url(project_url):
        print("a verified ChatGPT Work project URL is required", file=sys.stderr)
        return 2
    packet_path = Path(args.packet).expanduser()
    try:
        body = packet_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    receipt = f"WORK_CONSULT_RECEIPT: {secrets.token_hex(16)}"
    packet = f"{receipt}\n{body}"
    stderr_path = Path(args.stderr_output).expanduser()
    response_path = Path(args.response_output).expanduser()
    json_path = Path(args.json_output).expanduser()
    for path in (stderr_path, response_path, json_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    try:
        (
            submit_payload,
            response_payload,
            submit_elapsed,
            response_elapsed,
            transcript,
        ) = run_repl_streaming(
            build_repl_script(
                project_url=project_url,
                quality=args.quality,
                packet=packet,
                receipt=receipt,
                response_timeout_ms=args.response_timeout * 1000,
            ),
            submit_timeout=SUBMIT_TIMEOUT_SECONDS,
            response_timeout=args.response_timeout,
        )
    except SubmitUnknownError as exc:
        stderr_path.write_text(str(exc), encoding="utf-8")
        print(str(exc), file=sys.stderr)
        return 76
    except (TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        stderr_path.write_text(str(exc), encoding="utf-8")
        print(str(exc), file=sys.stderr)
        return 75
    stderr_path.write_text(transcript, encoding="utf-8")
    response_text = str(response_payload["responseText"])
    response_path.write_text(response_text + "\n", encoding="utf-8")
    evidence = {
        "ok": True,
        "receipt": receipt,
        "quality": args.quality,
        "model": submit_payload["model"],
        "tier": submit_payload["tier"],
        "conversationUrl": response_payload["conversationUrl"],
        "submitElapsedSeconds": round(submit_elapsed, 3),
        "responseElapsedSeconds": round(response_elapsed, 3),
        "responseOutput": str(response_path),
    }
    json_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CONSULT_COMPLETE response={response_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
