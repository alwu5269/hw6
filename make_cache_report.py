"""Write output/cache_test.md from output/cache_test.json."""
import json
from pathlib import Path

HERE = Path(__file__).parent
c = json.loads((HERE / "output" / "cache_test.json").read_text())
docs = sorted({x["document"] for x in c})
cost = lambda d, s: sum(x["cost_usd"] for x in c if x["document"] == d and x["setup"] == s)
tot = lambda s, k: sum(x[k] for x in c if x["setup"] == s)
rows, tn, tc = [], 0, 0
for d in docs:
    n, k = cost(d, "not_cached"), cost(d, "cached")
    tn, tc = tn + n, tc + k
    rows.append(f"| {d} | ${n:.6f} | ${k:.6f} | {100*(n-k)/n:.1f}% |")
rows.append(f"| **Total (12 docs)** | **${tn:.6f}** | **${tc:.6f}** | **{100*(tn-tc)/tn:.1f}%** |")
avgn, avgc = tn / 12, tc / 12
warm = sum(cost(d, "cached") for d in docs[1:]) / 11
N = 30000
cold = [x for x in c if x["setup"] == "cached" and x["call_in_run"] == 1 and x["cache_read_tokens"] == 0]
per_call_in = tot("cached", "input_tokens") / 24
n_in, n_r, n_w, n_o = (tot("not_cached", k) for k in ("input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens"))
c_in, c_r, c_w, c_o = (tot("cached", k) for k in ("input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens"))
zero_reads = sum(1 for x in c if x["setup"] == "not_cached" and x["cache_read_tokens"] == 0)
retried = sum(1 for x in c if x["attempt"] > 1)
md = f"""# Cache Test: with and without cached tokens

Setup: the vendor desk agent (no defense layers, `gpt-6-luna`) ran on all 12 practice documents twice. That is 48 model calls, because each run makes 2 calls: one to call `read_document`, one to answer.

- **not_cached:** a unique request id is placed at the very start of the prompt on every model call, so the API can never reuse a cached prefix. A not-cached run that showed any cached tokens would be thrown away and rerun. **All {zero_reads} of 24 not-cached calls reported 0 cache-read tokens**, so none had to be discarded ({retried} reruns needed).
- **cached:** the prompt is identical on every call, so the prefix (instructions, handbook, tool definitions) can be reused. {len(cold)} of the 24 cached calls started cold with 0 cache reads ({', '.join(x['document'].split('_')[0] for x in cold)}, the first call of the whole setup). Every other cached call read about 10.6k tokens from the cache.

Every call, with every token field the API reported and its cost from `data/prices.json`, is in `cache_test.json`.

## Token counts reported by the API (all 24 calls per setup)

| Setup | Input tokens | Cache read | Cache write | Output tokens |
|---|---|---|---|---|
| not_cached | {n_in:,} | {n_r:,} | {n_w:,} | {n_o:,} |
| cached | {c_in:,} | {c_r:,} | {c_w:,} | {c_o:,} |

"Input tokens" includes the cache read and cache write tokens. Cost = (input - read - write) at $0.10, reads at $0.01, writes at $0.125, and output at $0.50, all per 1M.

## Total cost per document

Each cost is for one run (2 model calls).

| Document | Not cached | Cached | Saved |
|---|---|---|---|
""" + "\n".join(rows) + f"""

Average per document: ${avgn:.6f} not cached, ${avgc:.6f} cached. Documents p02-p12 cost about ${warm:.6f} each with the cache warm.

## Actual vs. estimate

The Problem 2 estimate covered only the handbook: 7,300 tokens, so $0.00073 per call uncached and $0.000073 per call cached, which is about 90% saved.

| | Estimate (handbook only, per call) | Actual (per run, 2 calls) |
|---|---|---|
| Input tokens | 7,300 | about {c_in/12:,.0f} (about {per_call_in:,.0f} per call) |
| Uncached cost | $0.00073 per call, so $0.00146 per run | ${avgn:.6f} |
| Cached cost | $0.000073 per call, so $0.000146 per run | ${avgc:.6f} (about ${warm:.6f} warm) |
| Saved | about 90% | {100*(tn-tc)/tn:.1f}% (about {100*(avgn-warm)/avgn:.0f}% when warm) |

The actual numbers are higher than the estimate. The savings are close to it but a bit lower.

## Projection: 1,000 documents a day for 30 days ({N:,} documents)

| Scenario | Per document | 30 days |
|---|---|---|
| Without cache | ${avgn:.6f} | **${avgn*N:,.2f}** |
| With cache (warm, like p02-p12) | ${warm:.6f} | **${warm*N:,.2f}** |
| Saved | | ${(avgn-warm)*N:,.2f} ({100*(avgn-warm)/avgn:.0f}%) |

With the measured 12-document average (${avgc:.6f}, which includes one cold start) the cached total would be ${avgc*N:,.2f}. At 1,000 documents a day the cache would stay warm, so the warm figure is the better projection. This assumes a similar mix of documents and no change to the prompt.

## Surprises and why they happened

1. **Each document costs about 2x the prompt, not 1x.** The agent calls `read_document` first, so every document makes two model calls, and each one re-sends the whole prompt (about {per_call_in/1000:.1f}k tokens). That is why the 7,300-token estimate is too low.
2. **The prompt is bigger than the handbook alone.** About {per_call_in/1000:.1f}k tokens per call versus 7,300 estimated. The extra comes from the instructions, the tool and output schemas, and the document text. The 4-characters-per-token estimate also isn't exact.
3. **Not cached is more expensive than the plain input price.** Even with a unique prefix, the API reports {n_w:,} of the {n_in:,} input tokens as cache writes, which `prices.json` charges at $0.125 instead of $0.10. So the uncached setup pays a 25% premium on nearly every input token and costs more than the Problem 2 estimate assumed.
4. **Only the very first cached call was cold.** Its cache read was 0 and the whole prefix was written. After that, even the first call of each later run read the prefix from the cache. In the earlier run of this test the first two documents were cold. That difference is probably due to whether the prefix was still in the provider's cache from earlier runs, which I can't control or confirm.
5. **Cached calls still show some cache writes.** The second call of every run writes about 120-190 new tokens, which is the tool call and the document text appended after the shared prefix. Those tokens can't be read from cache yet, so they are billed at the write price.
6. **Cached savings are smaller than the 90% estimate.** Output tokens ({c_o:,}) cost the same in both setups and the new tokens in each call are always billed in full. That limits the warm savings to about {100*(avgn-warm)/avgn:.0f}%.
7. **Keeping the not-cached setup clean took care.** In an earlier run of this test, one not-cached call still read 10,772 tokens from the cache, which would not count. The runner now discards and reruns any not-cached run that shows cache reads. In this run none did, so every not-cached number is clean.
"""
(HERE / "output" / "cache_test.md").write_text(md)
print(md[md.index("## Total cost"):md.index("## Actual")])
print(f"{100*(tn-tc)/tn:.1f} {warm:.6f} {avgn*N:.2f} {warm*N:.2f}")
