# llmvis

CLI for measuring brand visibility in LLM responses.

## Quick start

```bash
python3 -m pip install .
llmvis auth connect --openai
llmvis queries add "best email marketing tool"
llmvis queries expand "CRM software" --review
llmvis scan --runs 3
llmvis report visibility --brand yourbrand.com
```

Phase 1 currently supports `chatgpt` only for scans.
