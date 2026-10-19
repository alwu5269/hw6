import argparse
import json
import os
import re
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools
from models import ExtractedFacts, VendorDecision
from tools import TRAP_FILE, approve_payment, read_document, send_email

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
OUTPUT = HERE / "output"
PRICE_KEY = "gpt-6-luna"  # key in data/prices.json
PORTKEY_MODEL = "gpt-6-luna"  # Portkey identifier (see AGENTS.md)
ALL_LAYERS = frozenset({"code", "design", "prompt"})


def load_env() -> None:
    """Load PORTKEY_API_KEY from hw6/.env, else the repository root .env, else the environment."""
    for env_file in (HERE / ".env", ROOT / ".env"):
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))
            break
    if not os.environ.get("PORTKEY_API_KEY"):
        raise SystemExit("PORTKEY_API_KEY is not set. Copy .env.example to .env and add your key.")


def prompt_section(name: str) -> str:
    text = (HERE / "prompts" / "prompt.md").read_text(encoding="utf-8")
    match = re.search(rf"<!-- {name} -->\n(.*?)(?=<!-- \w+ -->|\Z)", text, re.S)
    return match.group(1).strip() + "\n\n"


def build_model() -> OpenAIResponsesModel:
    load_env()
    return OpenAIResponsesModel(
        PORTKEY_MODEL,
        provider=OpenAIProvider(base_url="https://api.portkey.ai/v1", api_key=os.environ["PORTKEY_API_KEY"]),
    )


def build_agent(layers: frozenset = frozenset(), no_cache: bool = False) -> Agent:
    """Agent for one document. With the design layer it only extracts facts; otherwise it also decides."""
    handbook = (HERE / "data" / "shop_handbook.md").read_text(encoding="utf-8")
    if "design" in layers:
        instructions = prompt_section("extractor")
        output_type = ExtractedFacts
    else:
        instructions = prompt_section("base") + handbook
        output_type = VendorDecision
    if "prompt" in layers:
        instructions = prompt_section("defense") + instructions if "design" in layers else (
            instructions.replace("## Handbook", prompt_section("defense") + "## Handbook", 1)
        )
    if no_cache:
        # Evaluated on every model request: a unique first line changes the prompt prefix each time,
        # so the API cannot reuse a cached prefix (even between the two requests of one run).
        def request_id() -> str:
            return f"Request id: {uuid.uuid4().hex}\n\n"

        instructions = [request_id, instructions]
    return Agent(
        build_model(),
        output_type=output_type,
        instructions=instructions,
        # Design layer: the agent that reads the untrusted document can only read it. send_email and
        # approve_payment stay in tools.py but are not attached to it.
        tools=[read_document] if "design" in layers else [read_document, send_email, approve_payment],
    )


# ---- design layer: the model extracts, plain code applies the handbook rules ----

def _table_rows(section: str, handbook: str) -> list[list[str]]:
    body = re.search(rf"## {section}\..*?(?=\n## |\Z)", handbook, re.S).group(0)
    rows = [[c.strip() for c in line.strip("|").split("|")] for line in body.splitlines() if line.startswith("|")]
    return rows[2:]  # skip header and separator


def decide(facts: ExtractedFacts) -> VendorDecision:
    handbook = (HERE / "data" / "shop_handbook.md").read_text(encoding="utf-8")
    approved = [r[1].lower() for r in _table_rows("5", handbook)]
    blocked = [r[0].lower() for r in _table_rows("6", handbook)]
    max_cost = {r[0]: float(r[4].lstrip("$")) for r in _table_rows("9", handbook)}
    vendor = facts.vendor.strip().lower()

    def result(decision: str, reason: str) -> VendorDecision:
        return VendorDecision(**facts.model_dump(), decision=decision, reason=reason)

    if vendor in blocked:
        return result("do_not_recommend", f"Fails the approved-vendor check: {facts.vendor} is on the removed or pending list.")
    if vendor not in approved:
        return result("do_not_recommend", f"Fails the approved-vendor check: {facts.vendor} is not on the approved list.")
    limit = max_cost.get(facts.sku or "")
    if facts.unit_price is None or limit is None:
        return result("do_not_recommend", "Fails the price check: the unit price or the SKU's max unit cost is unknown.")
    if facts.unit_price > limit:
        return result("do_not_recommend", f"Fails the price check: the unit price is above the item's max unit cost.")
    if facts.lead_time_days is None or facts.lead_time_days > 21:
        return result("do_not_recommend", "Fails the lead-time check: the lead time is unknown or over 21 days.")
    if facts.min_order is None or facts.min_order > 600:
        return result("do_not_recommend", "Fails the minimum-order check: the minimum order is unknown or over 600 units.")
    return result("recommend", "The approved-vendor, price, lead-time, and minimum-order checks all pass.")


# ---- code layer: output guard ----

_LINK = re.compile(r"https?://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.-]+", re.I)


def guard_output(answer: VendorDecision, trap_calls: list) -> VendorDecision:
    """Strip links from the reason and fail closed if a trap tool was called."""
    reason = _LINK.sub("[link removed]", answer.reason)
    reason = re.split(r"(?<=[.!?])\s+", reason.strip())[0]
    if trap_calls:
        called = ", ".join(c["tool"] for c in trap_calls)
        return answer.model_copy(update={
            "decision": "do_not_recommend",
            "reason": f"Blocked: the document triggered a forbidden tool call ({called}).",
        })
    return answer.model_copy(update={"reason": reason})


# ---- running and logging ----

def append_json(path: Path, entry: dict) -> None:
    items = json.loads(path.read_text()) if path.exists() else []
    items.append(entry)
    path.write_text(json.dumps(items, indent=2) + "\n")


def cost_usd(usage) -> float:
    price = json.loads((HERE / "data" / "prices.json").read_text())[PRICE_KEY]
    cached = usage.cache_read_tokens
    written = usage.cache_write_tokens
    fresh = usage.input_tokens - cached - written
    return (
        fresh * price["input_per_1m"]
        + cached * price["cached_input_per_1m"]
        + written * price["cache_write_per_1m"]
        + usage.output_tokens * price["output_per_1m"]
    ) / 1_000_000


def tool_calls(messages) -> list[dict]:
    calls: dict[str, dict] = {}
    for msg in messages:
        if isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                    calls[part.tool_call_id] = {"tool": part.tool_name, "arguments": part.args_as_dict()}
        elif isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                    text = str(part.content)
                    calls[part.tool_call_id]["result"] = text if len(text) <= 200 else text[:200] + "..."
    return list(calls.values())


def run_document(doc: str, layers: frozenset = ALL_LAYERS) -> dict:
    """Run the agent on one document with the given defense layers. Returns answer, usage, and tool calls."""
    tools.SANITIZE = "code" in layers
    trap_before = len(json.loads(TRAP_FILE.read_text())) if TRAP_FILE.exists() else 0
    agent = build_agent(layers)
    start = time.monotonic()
    result = agent.run_sync(f"Review the vendor document at: {doc}")
    seconds = round(time.monotonic() - start, 2)
    answer = decide(result.output) if "design" in layers else result.output
    trap_calls = json.loads(TRAP_FILE.read_text())[trap_before:]
    if "code" in layers:
        answer = guard_output(answer, trap_calls)
    messages = result.all_messages()
    responses = [m.usage for m in messages if isinstance(m, ModelResponse)]
    totals = {
        "input_tokens": sum(u.input_tokens for u in responses),
        "cache_read_tokens": sum(u.cache_read_tokens for u in responses),
        "cache_write_tokens": sum(u.cache_write_tokens for u in responses),
        "output_tokens": sum(u.output_tokens for u in responses),
        "model_calls": len(responses),
        "cost_usd": round(sum(cost_usd(u) for u in responses), 8),
    }
    return {
        "answer": answer.model_dump(),
        "usage": totals,
        "seconds": seconds,
        "tool_calls": tool_calls(messages),
        "trap_calls": trap_calls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Campus Customs vendor desk agent")
    parser.add_argument("--doc", required=True, help="path to the vendor document")
    parser.add_argument("--layers", default="code,design,prompt", help="defense layers, comma-separated (or 'none')")
    args = parser.parse_args()
    layers = frozenset(l for l in args.layers.split(",") if l in ALL_LAYERS)

    run = run_document(args.doc, layers)
    now = datetime.now(timezone.utc).isoformat()
    append_json(OUTPUT / "usage_log.json", {
        "doc": args.doc,
        "time": now,
        "layers": sorted(layers),
        "seconds": run["seconds"],
        "input_tokens": run["usage"]["input_tokens"],
        "cached_input_tokens": run["usage"]["cache_read_tokens"],
        "output_tokens": run["usage"]["output_tokens"],
        "cost_usd": run["usage"]["cost_usd"],
    })
    append_json(OUTPUT / "audit_trail.json", {
        "doc": args.doc,
        "time": now,
        "layers": sorted(layers),
        "tool_calls": run["tool_calls"],
        "final_answer": run["answer"],
    })
    print(json.dumps(run["answer"], indent=2))


if __name__ == "__main__":
    main()
