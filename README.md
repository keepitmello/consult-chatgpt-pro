# consult-chatgpt-pro

A two-axis Consult package for obtaining a verified ChatGPT project Chat second
opinion through Aside.

- `consult/` is the normal Agent Skill. `SKILL.md` keeps only when, quality,
  packet, `consult` commands, and verification. Engine and recovery live in
  `consult/references/`.
- `consult/aside-skill/chatgpt-work-consult/` teaches Aside's own agent the
  stable project Chat browser workflow.
- `consult-playwright/` is the uninstalled agbrowse fallback. The main package
  carries only a hidden relative link to it for explicit failure recovery.

## Requirements

- Aside Browser CLI
- A ChatGPT account signed in inside Aside Browser
- Access to a ChatGPT project; set `CONSULT_CHATGPT_URL` and
  `CONSULT_PROJECT_NAME` in `~/.codex/consult.env`
- Python, Node.js, Chrome, and `agbrowse` only for the fallback

## Install

Clone the repository and link only the main skill:

```bash
git clone https://github.com/keepitmello/consult-chatgpt-pro.git
ln -s "$(pwd)/consult-chatgpt-pro/consult" ~/.agents/skills/consult
bash "$(pwd)/consult-chatgpt-pro/consult/scripts/install-aside-skill.sh"
bash "$(pwd)/consult-chatgpt-pro/consult/scripts/install-cli.sh"
```

Do not link `consult-playwright/` into a normal skill root. The main skill reads
its hidden fallback link only after the Aside path fails.

## Verify

Verify both axes:

```bash
node ~/.aside/u/0/skills/builtin/skill-creator/scripts/validate-frontmatter.mjs \
  consult/aside-skill/chatgpt-work-consult/SKILL.md
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s consult/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s consult-playwright/tests -q
```

## Usage

Read `consult/SKILL.md`. After `install-cli.sh`, `consult` is on PATH:

```bash
consult list
consult send --quality xhigh .consult/<run>/packet.md
consult send --quality xhigh .consult/<run>/packet.md --to <thread-id>
consult recover .consult/<run>/result.json
```

Every send must explicitly choose `xhigh` or `pro`; there is no default.
Engine, Chat surface, and recovery live in `consult/references/`.
Playwright is not an automatic sender.

## Security boundary

The skill automates the visible ChatGPT web UI. It does not use private ChatGPT endpoints, extract cookies or tokens, bypass access controls, or bundle browser credentials. Never put secrets, private keys, customer data, or unnecessary personal data in a consult packet.
