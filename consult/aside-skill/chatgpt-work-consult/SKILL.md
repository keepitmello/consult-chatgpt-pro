---
name: "chatgpt-work-consult"
description: "Send a packet into a new ChatGPT Work-project conversation, verify GPT-5.6 Sol at reasoning tier 매우 높음, wait for a terminal reply, and return the exact envelope. Use for ChatGPT Work consults, Work-project packet sends, and Aside work-consult result envelopes."
---

# ChatGPT Work Consult

Execute a packet consult on chatgpt.com inside the Work project. Do not rediscover the UI. Do not run this skill unless the task supplies an exact packet and exact receipt.

## Inputs

Accept the packet and receipt exactly as given in the task prompt. Do not rewrite, trim, wrap, or translate the packet.
`PACKET_BEGIN` and `PACKET_END` are transport delimiters; send only the text
between them.

## Browser and REPL

- Prefer an already logged-in chatgpt.com tab. If none exists, open `https://chatgpt.com`.
- Snapshot first. After every action, take a fresh snapshot and use only new refs.
- Do not declare reusable top-level `const` or `let` bindings. Store intermediate
  values on `globalThis` with a receipt-derived key, or use a fresh `var` name;
  the REPL scope persists across calls.

## Surface: Work project, new normal chat

1. Enter the ChatGPT project named **Work**.
2. Create a **new normal conversation** inside that project.
3. Never use temporary chat.
4. Never submit from global Chat.
5. Do not open or inspect unrelated existing conversations.
6. Before send, verify a visible Work project marker/breadcrumb **and** a project-owned composer.
7. If Work cannot be verified, stop before send.

Known project-home path:

1. Navigate directly to the supplied Work project URL. Ignore temporary/global
   Chat tabs rather than repairing them.
2. Require page title `ChatGPT - Work`, heading `Work`, and textbox
   `Work에서 새 채팅`. These three signals prove the project-owned composer.
3. The project-home composer itself starts a new Work conversation. Do not open
   an existing chat from the project list.

## Model and tier

Required state:

- Model: **GPT-5.6 Sol** checked
- Reasoning tier: **매우 높음**, shown as **4 of 5**

Rules:

- Verify GPT-5.6 Sol is checked.
- Verify the visible tier label is 매우 높음 (4 of 5).
- Never explore or select the fifth slider stop.
- If either state cannot be verified, stop before send.

Known picker path:

1. If the composer button already says `매우 높음`, click it once.
2. From that menu, open `모델 선택` and require the checked radio
   `GPT-5.6 Sol`.
3. Return to the simple tier view and require `매우 높음, 5개 중 4번째`.
4. Do not inspect the full page or probe alternative slider stops.

## Composer and send

1. Try a normal locator fill once.
2. If contenteditable fill fails, take a fresh snapshot, focus the project
   textbox, press `Meta+A`, press `Backspace`, then use keyboard `insertText`
   with the exact packet.
3. Read the textbox value/text back and require exact equality. If it differs,
   repeat that clear-and-insert sequence once after a fresh snapshot; then stop
   with an error rather than trying another input method.
4. Send only after the exact comparison and Work/model/tier checks pass.

## Wait and extract

- Wait until generation is terminal. Do not harvest a partial reply.
- Recover the exact assistant text from an accessibility snapshot.
- Use Copy only as an optional fallback if snapshot text is incomplete.
- Require the assistant reply to contain the exact receipt before reporting success.

## Output envelopes

Success, exact format:

```text
ASIDE_WORK_CONSULT_RESULT
RECEIPT: <exact receipt>
SURFACE: Work
MODEL: GPT-5.6 Sol
TIER: 매우 높음 (4 of 5)
RESPONSE_BEGIN
<exact ChatGPT response including its receipt>
RESPONSE_END
```

Failure, exact format:

```text
ASIDE_WORK_CONSULT_ERROR
RECEIPT: <exact receipt>
SURFACE: <last verified surface, or unknown>
BLOCKER: <concrete blocker>
```

Never fabricate response text. If Work, model, tier, composer, generation, or receipt matching fails, emit the error envelope and stop.
