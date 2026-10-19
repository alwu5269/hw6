# Cache Test: with and without cached tokens

Setup: the vendor desk agent (no defense layers, `gpt-6-luna`) ran on all 12 practice documents twice. That is 48 model calls, because each run makes 2 calls: one to call `read_document`, one to answer.

- **not_cached:** a unique request id is placed at the very start of the prompt on every model call, so the API can never reuse a cached prefix. A not-cached run that showed any cached tokens would be thrown away and rerun. **All 24 of 24 not-cached calls reported 0 cache-read tokens**, so none had to be discarded (0 reruns needed).
- **cached:** the prompt is identical on every call, so the prefix (instructions, handbook, tool definitions) can be reused. 1 of the 24 cached calls started cold with 0 cache reads (p01, the first call of the whole setup). Every other cached call read about 10.6k tokens from the cache.

Every call, with every token field the API reported and its cost from `data/prices.json`, is in `cache_test.json`.

## Token counts reported by the API (all 24 calls per setup)

| Setup | Input tokens | Cache read | Cache write | Output tokens |
|---|---|---|---|---|
| not_cached | 259,497 | 0 | 256,473 | 3,071 |
| cached | 258,958 | 243,250 | 12,684 | 2,729 |

"Input tokens" includes the cache read and cache write tokens. Cost = (input - read - write) at $0.10, reads at $0.01, writes at $0.125, and output at $0.50, all per 1M.

## Total cost per document

Each cost is for one run (2 model calls).

| Document | Not cached | Cached | Saved |
|---|---|---|---|
| p01_bluehen_quote.html | $0.002826 | $0.001566 | 44.6% |
| p02_elmcity_quote.html | $0.002850 | $0.000370 | 87.0% |
| p03_ivyprint_catalog.html | $0.003013 | $0.000560 | 81.4% |
| p04_harborstitch_quote.html | $0.002843 | $0.000386 | 86.4% |
| p05_maplemills_quote.pdf | $0.002789 | $0.000349 | 87.5% |
| p06_qtextile_quote.pdf | $0.002795 | $0.000320 | 88.5% |
| p07_longwharf_quote.pdf | $0.002808 | $0.000402 | 85.7% |
| p08_chapelst_email.eml | $0.002792 | $0.000309 | 88.9% |
| p09_westville_email.eml | $0.002790 | $0.000352 | 87.4% |
| p10_eastrock_email.eml | $0.002819 | $0.000348 | 87.7% |
| p11_yorkst_quote.html | $0.002777 | $0.000338 | 87.8% |
| p12_bluehen_quote.pdf | $0.002796 | $0.000386 | 86.2% |
| **Total (12 docs)** | **$0.033897** | **$0.005685** | **83.2%** |

Average per document: $0.002825 not cached, $0.000474 cached. Documents p02-p12 cost about $0.000374 each with the cache warm.

## Actual vs. estimate

The Problem 2 estimate covered only the handbook: 7,300 tokens, so $0.00073 per call uncached and $0.000073 per call cached, which is about 90% saved.

| | Estimate (handbook only, per call) | Actual (per run, 2 calls) |
|---|---|---|
| Input tokens | 7,300 | about 21,580 (about 10,790 per call) |
| Uncached cost | $0.00073 per call, so $0.00146 per run | $0.002825 |
| Cached cost | $0.000073 per call, so $0.000146 per run | $0.000474 (about $0.000374 warm) |
| Saved | about 90% | 83.2% (about 87% when warm) |

The actual numbers are higher than the estimate. The savings are close to it but a bit lower.

## Projection: 1,000 documents a day for 30 days (30,000 documents)

| Scenario | Per document | 30 days |
|---|---|---|
| Without cache | $0.002825 | **$84.74** |
| With cache (warm, like p02-p12) | $0.000374 | **$11.23** |
| Saved | | $73.51 (87%) |

With the measured 12-document average ($0.000474, which includes one cold start) the cached total would be $14.21. At 1,000 documents a day the cache would stay warm, so the warm figure is the better projection. This assumes a similar mix of documents and no change to the prompt.

## Surprises and why they happened

1. **Each document costs about 2x the prompt, not 1x.** The agent calls `read_document` first, so every document makes two model calls, and each one re-sends the whole prompt (about 10.8k tokens). That is why the 7,300-token estimate is too low.
2. **The prompt is bigger than the handbook alone.** About 10.8k tokens per call versus 7,300 estimated. The extra comes from the instructions, the tool and output schemas, and the document text. The 4-characters-per-token estimate also isn't exact.
3. **Not cached is more expensive than the plain input price.** Even with a unique prefix, the API reports 256,473 of the 259,497 input tokens as cache writes, which `prices.json` charges at $0.125 instead of $0.10. So the uncached setup pays a 25% premium on nearly every input token and costs more than the Problem 2 estimate assumed.
4. **Only the very first cached call was cold.** Its cache read was 0 and the whole prefix was written. After that, even the first call of each later run read the prefix from the cache. In the earlier run of this test the first two documents were cold. That difference is probably due to whether the prefix was still in the provider's cache from earlier runs, which I can't control or confirm.
5. **Cached calls still show some cache writes.** The second call of every run writes about 120-190 new tokens, which is the tool call and the document text appended after the shared prefix. Those tokens can't be read from cache yet, so they are billed at the write price.
6. **Cached savings are smaller than the 90% estimate.** Output tokens (2,729) cost the same in both setups and the new tokens in each call are always billed in full. That limits the warm savings to about 87%.
7. **Keeping the not-cached setup clean took care.** In an earlier run of this test, one not-cached call still read 10,772 tokens from the cache, which would not count. The runner now discards and reruns any not-cached run that shows cache reads. In this run none did, so every not-cached number is clean.
