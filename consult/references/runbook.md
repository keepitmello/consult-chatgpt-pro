# Aside Work Consult Runbook

## Preconditions

- `aside --version` succeeds.
- `~/.aside/u/0/skills/user/chatgpt-work-consult/SKILL.md` exists and validates.
- `CONSULT_CHATGPT_URL` resolves to the ChatGPT project named `Work`.
- The packet is self-contained and safe to disclose to Aside and ChatGPT.

If the Aside account skill is missing, run:

```bash
bash <consult-skill-dir>/scripts/install-aside-skill.sh
```

Fail before `aside exec` unless the URL matches:

```text
https://chatgpt.com/g/g-p-...-work/project
```

Global `/`, global `/c/...`, temporary chat, a non-HTTPS URL, or another host is
not a recoverable default.

## Build the Aside brief

Generate a random receipt and write one run-specific task file. Include the
packet body verbatim rather than asking Aside to discover a local file.

```text
Read your account skill `chatgpt-work-consult` before any browser action.

Work project URL: <CONSULT_CHATGPT_URL>
Receipt: <random receipt>

Execute that skill with the exact packet below.

PACKET_BEGIN
<exact packet>
PACKET_END
```

The delimiters belong to the Aside transport brief. The ChatGPT composer must
receive only `<exact packet>`.

Launch it in a persistent PTY:

```bash
aside exec --effort high "$(<.consult/<run>/aside-task.txt)"
```

The harness background process completion is the normal terminal signal. Follow
the Aside skill's progress-reporting rule; do not poll snapshots in a tight loop.

## Accept or reject

Accept only:

```text
ASIDE_WORK_CONSULT_RESULT
RECEIPT: <exact receipt>
SURFACE: Work
MODEL: GPT-5.6 Sol
TIER: 매우 높음 (4 of 5)
RESPONSE_BEGIN
<exact response containing the receipt>
RESPONSE_END
```

Reject a missing/mismatched receipt, any other surface, an unverified model or
tier, a partial response, or an `ASIDE_WORK_CONSULT_ERROR`.

On rejection, preserve the Aside output. Read
`fallback/consult-playwright/SKILL.md` only when a Playwright fallback is
actually needed.
