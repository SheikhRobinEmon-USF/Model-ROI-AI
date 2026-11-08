# Studio model selection

The active studio uses Ollama on localhost. Qwen3 4B and Gemma 4 E4B generate answers. OpenAI gpt-oss-20b runs locally as the sole grader and comparison summarizer. These calls incur zero hosted API charges. Model downloads, runtime memory, electricity and hardware are separate considerations.

## Historical hosted pilot proposal

Checked 2026-11-06. Provisional pair: OpenAI GPT-6 Luna and Anthropic Claude Haiku 5.5. Both list standard short-context text pricing of $0.10 input / $0.50 output per million tokens. This is a cost-based shortlist, not measured quality superiority.

Sources:
- https://openai.com/api/
- https://developers.openai.com/api/docs/pricing
- https://www.anthropic.com/claude/haiku
- https://platform.claude.com/docs/en/about-claude/pricing

Illustrative workload: 15 people, one 50-case experiment per person, 1,000 input and 300 billed output tokens per case per model. Each model costs $0.1875; the pair costs $0.375. At 10 people the pair costs $0.25. Excludes retries, additional reasoning tokens, hosting, tax, tools and repeated runs. Actual usage differs by tokenizer.

Public visitors should inspect stored benchmarks or mocks, as the approved contract requires. Those visits incur no provider inference spend. Owner-only experiments generate the historical evidence. Suggested initial owner budget: $5 total, pending explicit approval. No paid execution is enabled.

Quality and latency rankings require matched real runs. Neither provider's marketing establishes accuracy on this project's tasks.

Status: adapter mapping tested with simulated responses. SDK installation, real credentials, bounded pricing integration, orchestration and live provider compatibility still need validation.
