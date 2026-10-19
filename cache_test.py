"""Run the agent on every practice document with and without prompt caching."""
import json
from pathlib import Path

from pydantic_ai.messages import ModelResponse

from agent import build_agent, cost_usd

HERE = Path(__file__).parent
docs = sorted((HERE / "data" / "practice_docs").iterdir())
docs = [d for d in docs if d.suffix in (".html", ".pdf", ".eml")]
assert len(docs) == 12

calls = []


def run(setup: str, doc: Path, agent) -> None:
    for attempt in range(1, 6):
        new = run_once(setup, doc, agent)
        # A not-cached run that still shows cached tokens does not count: discard it and run again.
        if setup != "not_cached" or all(c["cache_read_tokens"] == 0 for c in new):
            break
        print("  discarded: not_cached run showed cache reads, retrying", flush=True)
    else:
        raise SystemExit(f"{doc.name}: could not get a not_cached run with zero cache reads")
    for c in new:
        c["attempt"] = attempt
    calls.extend(new)
    print(setup, doc.name, "ok", flush=True)


def run_once(setup: str, doc: Path, agent) -> list:
    result = agent.run_sync(f"Review the vendor document at: {doc.relative_to(HERE)}")
    new = []
    n = 0
    for msg in result.all_messages():
        if isinstance(msg, ModelResponse):
            n += 1
            u = msg.usage
            new.append({
                "setup": setup,
                "document": doc.name,
                "call_in_run": n,
                "input_tokens": u.input_tokens,
                "cache_read_tokens": u.cache_read_tokens,
                "cache_write_tokens": u.cache_write_tokens,
                "output_tokens": u.output_tokens,
                "details": u.details,
                "cost_usd": round(cost_usd(u), 8),
            })
    return new


# Not cached: a fresh request id per model request makes the prompt prefix unique, so nothing can be reused.
for doc in docs:
    run("not_cached", doc, build_agent(no_cache=True))

# Cached: identical prompt prefix every call.
cached_agent = build_agent()
for doc in docs:
    run("cached", doc, cached_agent)

(HERE / "output" / "cache_test.json").write_text(json.dumps(calls, indent=2) + "\n")
