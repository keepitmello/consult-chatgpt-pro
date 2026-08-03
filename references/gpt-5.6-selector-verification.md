# GPT-5.6 selector verification

Verified 2026-07-11 against local `agbrowse` 0.1.16 and the visible ChatGPT Work model picker.

- `--quality high` -> official agbrowse `thinking` + `high` -> visible GPT-5.6 Thinking / High
- `--quality xhigh` -> official agbrowse `thinking` + `xhigh` -> visible GPT-5.6 Thinking / Extra High
- `--quality pro` -> official agbrowse `pro` with no separate effort -> visible GPT-5.6 Pro
- Version-pinned requests require the exact `GPT-5.6` family row. Missing family, model, effort, or post-click verification aborts before send.
- Require agbrowse 0.1.18 or newer; it owns GPT-5.6 picker support, so do not restore the removed local GPT-5.6 model aliases.

Selector probes use `agbrowse web-ai status` attached to the shared headed profile on port 9222 after `scripts/ensure_consult_chrome.py --ensure`. The live smoke used `scripts/run_agbrowse_consult.py --quality xhigh` with all outputs isolated under `/tmp`.
