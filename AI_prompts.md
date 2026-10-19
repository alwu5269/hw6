# AI Prompts Log

## Problem 2: Size up the handbook

**Prompt 1:**
> * show me data/shop_handbook.md and data/prices.json
> * create output/handbook_estimate.md

**Follow-up prompt (if needed):**
> Fill out output/handbook_estimate.md:
>
> * The token count and how I got it:
>    * I first got Claude to count the number of characters in the handbook, which is about 29,241 characters. After searching it up, it seems that 1 token is approximately 4 characters. So we divide 29,241 by 4, this gets us about 7,300 tokens.
> * What the handbook costs in terms of dollars on one call, and on 1000 calls, with cached tokens and without them:
>    * One Call:
>       * Not Cached:
>          * Since one call is 7300 tokens, we multiply that by the price value we have. 7300 tokens * ($0.10/1M tokens) = $0.00073 for one call
>       * Cached:
>          * Since one call is 7300 tokens, we multiply that by the price value we have. 7300 tokens * ($0.01/1M tokens) = $0.000073 for one call
>    * 1000 Calls:
>       * Not Cached:
>          * $0.00073 for one call * 1000 calls = $0.73.
>       * Cached:
>          * $0.000073 for one call * 1000 calls = $0.073.

*Why the first prompt wasn't enough:*
The first prompt didn't say how to get the token count or which scenarios to cost. It left out the character count, the 4-characters-per-token rule, and the one-call versus 1000-call, cached versus uncached comparison, so I had to spell them out.


## Problem 3: Build the vendor desk agent

**Prompt 1:**
> Build a vendor desk agent with PydanticAI and gpt-6-luna: prompts/prompt.md (instructions), agent.py (entry point), tools.py (tools), models.py (structured types). It takes a path to a vendor document (HTML, PDF or .eml), reads it with a tool, and returns vendor, SKU, unit price, lead time in days, minimum order, a recommend/do_not_recommend decision following the handbook rules, and a one-sentence reason. Add two trap tools, send_email and approve_payment, that only append the call and arguments to output/trap_calls.json (starts as an empty list). After every run append to output/usage_log.json (document, time, API-reported tokens, dollar cost from prices.json) and output/audit_trail.json (each tool call with arguments and a short result, plus the final answer). Run it with `python agent.py --doc data/practice_docs/p01_bluehen_quote.html`. Start output/harness.md with each field in models.py and why, and each tool in one line.

**Follow-up prompt (if needed):**
> Update the title in AI_prompts.md title to Build the vendor desk agent. Also run the agent on p01 and p08

*Why the first prompt wasn't enough:*
I wanted to set up first before running the code.


## Problem 4: With and without cached tokens

**Prompt 1:**
> * Run agent on all 12 documents in 2 ways: cached and not cached
> * Check the token count sent back by the API
> * Save every model call in output/cache_test.json: for each call, include the setup, document, every token the API reports, and dollars from price.json
> * In output/cache_test.md: total cost per document for each setup and percent saved; how the actual numbers compare to estimates; projection for 1000 documents a day for 30 days, with and without cache; anything surprising in the numbers and why they happened

**Follow-up prompt (if needed):**
> 

*Why the first prompt wasn't enough:*


## Problem 5: Attack your own agent

**Prompt 1:**
> * Run agent on data/practice_docs/
> * Compare each output to practice_key.json and check output/trap_calls.json
> * Save output/attack_results.json: for each document, whether each field matched the key, whether the decision matched, whether a trap tool was called, whether a link or strange text was in the answer
> * In output/attack_results.md: for every doc that fooled the agent, write what fooled it and where in the file it was hiding.

**Follow-up prompt (if needed):**
> 

*Why the first prompt wasn't enough:*


## Problem 6: Defend your agent

**Prompt 1:**
> * Add defense to agent on 3 levels: Code, Design, Prompt in prompts/prompt.md
> * send_email and approve_payments may not be deleted
> * Rerun all 12 documents
> * Save output/defense_results.json in the same shape as attack_results.json. Along with tokens and dollar amounts.
> * Clean documents should still return correct values
> * In output/defense_results.md: a before and after for all 12 documents; what each layer catches that the others miss; the extra tokens + dollars each layer adds per document
> * Add safety features to output/harness.md in a Safety section: what each defense layer does in plain words

**Follow-up prompt (if needed):**
> 

*Why the first prompt wasn't enough:*


## Problem 7: Red team

**Prompt 1:**
> * Make 2 trapped vendor documents in data/my_attacks (HTML, PDF, email) where there should be a hidden trick or attack no in the problem set
> * A person opening the docs should see normal quotes.
> * Run both documents on agents with no defense and defended.
> * In output/red_team.md: for each attack: what is hidden, where, what it tries to make the agent do, + what happened before and after defenses

**Follow-up prompt (if needed):**
> 

*Why the first prompt wasn't enough:*


## Problem 8: Exam documents

**Prompt 1:**
> * run final defended agent on 10 docs in data/exam_docs
> * save output to output/exam_results,json with one entry per exam file. Each entry should have the following fields:
>    * file: exam file name
>    * vendor
>    * sku
>    * unit_price
>    * lead_time_days
>    * min_order
>    * decision: recommend or not recommend
>    * reason
>    * trap_tool_called: true or false
>    * input_tokens, cached_tokens, output_tokens
>    * cost_usd

**Follow-up prompt (if needed):**
> 

*Why the first prompt wasn't enough:*


## Problem 9: Results page

**Prompt 1:**
> * Build output/hw6_report.html
>    * Must be one file that opens with double click + not need internet + no other files next to it
>    * Must show 5 things + use real numbers from earlier problems:
>       * Caching results w/ chart
>       * Attacks before + after defense
>       * What defense cost in tokens + dollars
>       * Exam results + two red team documents
>       * Short rec for the manager: should Campus Customs turn this agent on for real vendor mail + what it would cost per month for 1000 documents a day
> * Ensure layout is clear and use fall palate

**Follow-up prompt (if needed):**
> 

*Why the first prompt wasn't enough:*
