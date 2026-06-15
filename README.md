# Lemonade Agents

GAIA agent entry points for the Lemonade Store suite.

This repo is the explicit heavy bridge layer. It depends on `amd-gaia`
and uses the local Lemonade SDK server for model calls. Department repos
should not require this package in their base installs; they should keep
it behind an optional `agents` extra.

## Offline Runtime

Agents default to local Lemonade SDK/GAIA settings:

- `LEMONADE_BASE_URL`: local Lemonade server URL. If unset, GAIA's
  `DEFAULT_LEMONADE_URL` is used.
- `LEMONADE_MODEL`: local model ID. If unset, GAIA's
  `DEFAULT_MODEL_NAME` is used.
- Cloud providers are disabled in the shared base agent with
  `use_claude=False` and `use_chatgpt=False`.

Run the Lemonade SDK server locally before starting an agent. On this
workstation that usually means `lemond` or the equivalent Lemonade app
launcher, with model assets already present for offline use.

## Install

Install this package only where agent execution is needed:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Department repos use:

```bash
make install-agents
```

## Entry Points

GAIA discovers the department agents through the `gaia.agents` entry
point group:

- `lemonade-helper`
- `lemonade-cashier`
- `lemonade-inventory`
- `lemonade-accounting`
- `lemonade-marketeer`
- `lemonade-supplier`
- `lemonade-reports`
- `lemonade-security`

Each script entry point has the same name and can be used for direct
local smoke checks.
