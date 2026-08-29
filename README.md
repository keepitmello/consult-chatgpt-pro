# consult-chatgpt-pro

A two-axis Consult package for obtaining a verified ChatGPT Work-project second
opinion through Aside.

- `consult/` is the normal Agent Skill. It owns packet quality, receipts, saved
  evidence, and local verification.
- `consult/aside-skill/chatgpt-work-consult/` teaches Aside's own agent the
  stable Work-project browser workflow.
- `consult-playwright/` is the uninstalled agbrowse fallback. The main package
  carries only a hidden relative link to it for explicit failure recovery.

## Requirements

- Aside Browser CLI
- A ChatGPT account signed in inside Aside Browser
- Access to the ChatGPT project named `Work`
- Python, Node.js, Chrome, and `agbrowse` only for the fallback

## Install

Clone the repository and link only the main skill:

```bash
git clone https://github.com/keepitmello/consult-chatgpt-pro.git
ln -s "$(pwd)/consult-chatgpt-pro/consult" ~/.agents/skills/consult
bash "$(pwd)/consult-chatgpt-pro/consult/scripts/install-aside-skill.sh"
```

Do not link `consult-playwright/` into a normal skill root. The main skill reads
its hidden fallback link only after the Aside path fails.

## Verify

Verify both axes:

```bash
node ~/.aside/u/0/skills/builtin/skill-creator/scripts/validate-frontmatter.mjs \
  consult/aside-skill/chatgpt-work-consult/SKILL.md
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s consult-playwright/tests -q
```

## Usage

Read `consult/SKILL.md`. Normal advice consults delegate to Aside and run only
inside Work. The fallback retains the old strict picker, session, attachment,
and code-artifact machinery.

## Security boundary

The skill automates the visible ChatGPT web UI. It does not use private ChatGPT endpoints, extract cookies or tokens, bypass access controls, or bundle browser credentials. Never put secrets, private keys, customer data, or unnecessary personal data in a consult packet.
