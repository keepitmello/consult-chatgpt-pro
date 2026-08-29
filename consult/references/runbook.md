# Aside Work Consult Runbook

## Preconditions

- `aside --version` succeeds.
- `~/.aside/u/0/skills/user/chatgpt-work-consult/SKILL.md` exists and validates.
- `CONSULT_CHATGPT_URL` resolves to the ChatGPT project named `Work`.
- The invocation contains exactly one `--quality xhigh` or `--quality pro`.
- The packet is self-contained and safe to disclose to Aside and ChatGPT.

If the Aside account skill is missing, run:

```bash
bash <consult-skill-dir>/scripts/install-aside-skill.sh
```

Fail before the REPL runner unless the URL matches:

```text
https://chatgpt.com/g/g-p-...-work/project
```

Global `/`, global `/c/...`, temporary chat, a non-HTTPS URL, or another host is
not a recoverable default.

## Launch the fast path

Launch the deterministic Aside REPL runner as a background process:

```bash
python3 <consult-skill-dir>/scripts/run_aside_repl_consult.py \
  --quality <xhigh-or-pro> \
  --packet .consult/<run>/packet.md \
  --response-output .consult/<run>/response.md \
  --json-output .consult/<run>/result.json \
  --stderr-output .consult/<run>/stderr.log
```

The runner's in-browser guard must commit the user turn within 120 seconds and
records `submitElapsedSeconds`; it exits `75` at that boundary. Never increase
or blindly retry the budget. Aside CLI can buffer `CONSULT_SUBMITTED` until the
response finishes, so the saved timing is authoritative. Aside REPL does not
create a normal Aside GUI conversation entry.

Exit `76` is `SUBMIT_UNKNOWN`: the click occurred but the user turn was not
commit-verified before the deadline. Preserve its evidence and never retry,
invoke the Aside agent, or enter the Playwright fallback.

## Accept or reject

For `--quality xhigh`, require:

```text
quality: xhigh
model: GPT-5.6 Sol
tier: 매우 높음 (4 of 5)
submitElapsedSeconds: <120
```

For `--quality pro`, require:

```text
quality: pro
model: GPT-5.6 Sol
tier: Pro (5 of 5)
submitElapsedSeconds: <120
```

Reject a missing or mismatched quality/receipt, an unverified model or tier, a
partial response, or a submission at or above 120 seconds.

On exit `75` caused by verified UI drift, preserve evidence and use `aside exec`
plus `chatgpt-work-consult` once as adaptive recovery. Only then read
`fallback/consult-playwright/SKILL.md`.
