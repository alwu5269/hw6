"""Run the final defended agent on every document in data/exam_docs."""
import json
from pathlib import Path

from agent import ALL_LAYERS, run_document

HERE = Path(__file__).parent
docs = sorted(p for p in (HERE / "data" / "exam_docs").iterdir() if p.suffix in (".html", ".pdf", ".eml"))
assert len(docs) == 10
results = []
for doc in docs:
    run = run_document(f"data/exam_docs/{doc.name}", ALL_LAYERS)
    a, u = run["answer"], run["usage"]
    results.append({
        "file": doc.name,
        "vendor": a["vendor"],
        "sku": a["sku"],
        "unit_price": a["unit_price"],
        "lead_time_days": a["lead_time_days"],
        "min_order": a["min_order"],
        "decision": a["decision"],
        "reason": a["reason"],
        "trap_tool_called": bool(run["trap_calls"]),
        "input_tokens": u["input_tokens"],
        "cached_tokens": u["cache_read_tokens"],
        "output_tokens": u["output_tokens"],
        "cost_usd": u["cost_usd"],
    })
    print(doc.name, a["decision"], bool(run["trap_calls"]), flush=True)
(HERE / "output" / "exam_results.json").write_text(json.dumps(results, indent=2) + "\n")
