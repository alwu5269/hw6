# Handbook Size and Cost Estimate

## Token count and how I got it

- I had Claude count the characters in `data/shop_handbook.md`: **29,241 characters**.
- A common rule of thumb is that 1 token is about 4 characters.
- 29,241 / 4 = 7,310, so the handbook is about **7,300 tokens**.

Price used (`data/prices.json`, gpt-6-luna, per 1M tokens): input $0.10, cached input $0.01.

## Cost of the handbook as input

### One call

| Case | Math | Cost |
|---|---|---|
| Not cached | 7,300 tokens × ($0.10 / 1M) | **$0.00073** |
| Cached | 7,300 tokens × ($0.01 / 1M) | **$0.000073** |

### 1,000 calls

| Case | Math | Cost |
|---|---|---|
| Not cached | $0.00073 × 1,000 | **$0.73** |
| Cached | $0.000073 × 1,000 | **$0.073** |

Caching makes the handbook's input cost 10x cheaper. These figures cover only the handbook. They leave out the vendor document, the output tokens, and the one-time cache write ($0.125 per 1M, about $0.00091).

*The token count is an estimate from character count. Use the API's reported usage for exact numbers.*
