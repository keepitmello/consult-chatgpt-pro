---
name: consult
description: "Aside를 통해 ChatGPT Work 프로젝트에 패킷을 보내고 답을 검증한다. 일반 상담·리서치·설계 검토의 기본 경로."
---

# Consult

Send one self-contained packet to ChatGPT through Aside. The outer agent owns
the question, packet, receipt, saved evidence, and local verification. The
deterministic Aside REPL runner owns the normal **Work** project path; Aside's
`chatgpt-work-consult` agent skill owns UI-drift recovery only.

## Workflow

1. Require exactly one explicit `--quality xhigh` or `--quality pro` flag.
   With no flag, both flags, or any other value, stop before writing a packet or
   opening Aside.
2. State one precise question and what the answer must settle.
3. Write a focused packet with the decisive evidence, constraints, failed
   attempts, and acceptance criteria. Check it for secrets and stale context.
   Ask for a natural Korean report while leaving structure and terminology to
   the consultant.
4. Launch `scripts/run_aside_repl_consult.py` as a persistent background
   process with the exact quality and packet paths. The deterministic Aside REPL
   fast path owns Work navigation, tier/model verification, send, terminal
   wait, receipt recovery, and artifacts. Its in-browser guard must commit the
   user turn in under 60 seconds or exit `75`; never extend or retry that
   submission budget. Aside CLI may buffer `CONSULT_SUBMITTED` until completion,
   so use the recorded `submitElapsedSeconds` as the timing evidence.
   Exit `76` means the send was clicked but commit could not be proven; preserve
   evidence and never retry or enter any fallback because that could duplicate
   the turn.
5. Read the saved response and JSON evidence. Require the receipt and quality
   to match the invocation.
   Before launch, reject a URL unless it is HTTPS on `chatgpt.com`, its path
   starts with `/g/g-p-`, contains `-work/`, and ends in `/project`.
6. For `xhigh`, require `GPT-5.6 Sol` and
   `매우 높음 (4 of 5)`. For `pro`, require `GPT-5.6 Sol` and
   `Pro (5 of 5)`. Read the exact answer from the saved response file.
7. Verify every material claim locally before acting on it.

Never use temporary chat or global Chat. Never submit when the Work project,
model, tier, or receipt is unverified.

`references/runbook.md` contains the exact Aside brief and recovery contract.
`references/context-checklist.md` helps with complex packets.
`references/after-advice.md` governs local use of the answer.

## Fallback

Do not load the Playwright implementation during a normal consult. If Aside
REPL exits `75` because verified UI structure changed, read Skill(aside-browser)
and run `aside exec` with the installed `chatgpt-work-consult` skill as the
adaptive recovery path. Do not use an Aside agent for ordinary sends. If that
recovery also returns `ASIDE_WORK_CONSULT_ERROR`, or the task requires a code
artifact Aside cannot retrieve, then read `fallback/consult-playwright/SKILL.md`
and use that hidden fallback explicitly.

## Completion

Report the question, Work/model/tier evidence, matching receipt, advice accepted
or rejected, local verification, and remaining uncertainty.
