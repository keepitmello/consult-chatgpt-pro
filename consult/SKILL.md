---
name: consult
description: "Aside를 통해 ChatGPT Work 프로젝트에 패킷을 보내고 답을 검증한다. 일반 상담·리서치·설계 검토의 기본 경로."
---

# Consult

Send one self-contained packet to ChatGPT through Aside. The outer agent owns
the question, packet, receipt, saved evidence, and local verification. Aside's
`chatgpt-work-consult` skill owns browser operation inside the **Work** project.

## Workflow

1. State one precise question and what the answer must settle.
2. Write a focused packet with the decisive evidence, constraints, failed
   attempts, and acceptance criteria. Check it for secrets and stale context.
   Ask for a natural Korean report while leaving structure and terminology to
   the consultant.
3. Read Skill(browser-cli), then Skill(aside-browser). Use `aside exec` as a
   persistent background PTY process.
4. Give Aside:
   - an exact random receipt;
   - the exact packet text;
   - the Work project URL from `CONSULT_CHATGPT_URL` or
     `~/.codex/consult.env`;
   - an explicit instruction to read its account skill
     `chatgpt-work-consult` before any browser action.
   Before launch, reject a URL unless it is HTTPS on `chatgpt.com`, its path
   starts with `/g/g-p-`, contains `-work/`, and ends in `/project`.
5. Accept only an `ASIDE_WORK_CONSULT_RESULT` envelope whose receipt matches,
   `SURFACE` is `Work`, `MODEL` is `GPT-5.6 Sol`, and `TIER` is `매우 높음`
   (4 of 5). Save the exact text between `RESPONSE_BEGIN` and `RESPONSE_END`.
6. Verify every material claim locally before acting on it.

Never use temporary chat or global Chat. Never submit when the Work project,
model, tier, or receipt is unverified.

`references/runbook.md` contains the exact Aside brief and recovery contract.
`references/context-checklist.md` helps with complex packets.
`references/after-advice.md` governs local use of the answer.

## Fallback

Do not load the Playwright implementation during a normal consult. If Aside
returns `ASIDE_WORK_CONSULT_ERROR`, its result envelope is invalid, or the task
requires a code artifact Aside cannot retrieve, then read
`fallback/consult-playwright/SKILL.md` and use that hidden fallback explicitly.

## Completion

Report the question, Work/model/tier evidence, matching receipt, advice accepted
or rejected, local verification, and remaining uncertainty.
