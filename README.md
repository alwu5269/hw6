# HW6: Campus Customs Vendor Desk Agent

A PydanticAI agent that reads one vendor document (HTML, PDF or `.eml`), pulls out the vendor, SKU, unit price, lead time and minimum order, and decides `recommend` or `do_not_recommend` using the rules in `data/shop_handbook.md`. It calls `gpt-6-luna` through Portkey.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your own PORTKEY_API_KEY in .env
```

## Run the agent

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html
```

The defended agent (code, design and prompt layers) runs by default. Choose layers with `--layers`, for example `--layers none` for the undefended Problem 3 agent or `--layers prompt` for one layer:

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html --layers none
```

Each run prints the answer and appends to `output/usage_log.json` (tokens and cost) and `output/audit_trail.json` (tool calls and final answer). The trap tools `send_email` and `approve_payment` only append to `output/trap_calls.json`.

## Files

- `agent.py`: entry point and defense layers. `tools.py`: document reader and trap tools. `models.py`: output types. `prompts/prompt.md`: instructions.
- Scripts that produced the outputs: `cache_test.py` (Problem 4), `attack_test.py` (Problem 5), `defense_test.py` (Problem 6), `red_team_test.py` (Problem 7), `run_exam.py` (Problem 8), plus `make_cache_report.py` and `make_defense_report.py`.
- `output/hw6_report.html`: the results page. Open it in any browser, no internet needed.

Rerunning `attack_test.py` or `defense_test.py` resets `output/trap_calls.json` to `[]`.
