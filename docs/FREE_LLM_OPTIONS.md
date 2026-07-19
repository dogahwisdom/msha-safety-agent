# Free LLM options for this project

You do **not** need a paid OpenAI account to run the agent or benchmark. This repo supports three paths, ordered by quality for function-calling agents:

## Recommended: Groq (free cloud API, no credit card)

| | |
|---|---|
| **Cost** | Free tier — no credit card required |
| **Sign up** | [console.groq.com](https://console.groq.com) |
| **Quality** | **Llama 3.3 70B** — much stronger than local 7B models for tool selection |
| **Limits** | ~30 requests/min, ~1,000 requests/day on 70B (enough for one 60-question benchmark) |
| **Setup** | OpenAI-compatible — already wired in |

```bash
# In .env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
```

Then run:

```bash
python eval/run_benchmark.py
python eval/score.py
```

## Local: Ollama (100% free, runs on your machine)

| | |
|---|---|
| **Cost** | Free |
| **Quality** | Depends on model; `qwen2.5:7b` works but may misread tool output |
| **Speed** | Slower on CPU; no daily caps |
| **Setup** | Auto-detected when Ollama is running on port 11434 |

```bash
ollama pull qwen2.5:7b
export OLLAMA_MODEL=qwen2.5:7b
export LLM_PROVIDER=ollama
python -m src.agent.run_agent "How many fatalities occurred in 2015?"
```

For better local quality (if your machine has RAM/GPU): `ollama pull llama3.3:70b`

## Offline tools (no LLM at all)

For reproducible paper numbers without any API:

```bash
export LLM_PROVIDER=offline
python eval/run_benchmark.py
python eval/score.py
```

Uses category-based tool routing (`OfflineToolAgent`). Fast, deterministic, no hallucination — but not true natural-language understanding.

## Other options (not built in, but worth knowing)

| Provider | Free? | Notes |
|----------|-------|-------|
| **Google Gemini** | Free tier at [ai.google.dev](https://ai.google.dev) | Different API; would need a separate client adapter |
| **OpenRouter** | Some free models | OpenAI-compatible; add `OPENROUTER_API_KEY` + base URL manually |
| **Hugging Face Inference** | Limited free tier | Slower; not OpenAI-compatible by default |
| **xAI Grok** | **Not free** | Requires X Premium / paid API — not a budget option |

**Grok is not a free alternative.** Groq (with a **q**) is the free fast-inference provider this repo supports.

## Provider priority (`LLM_PROVIDER=auto`, default)

1. `OPENAI_API_KEY` → OpenAI (paid)
2. `GROQ_API_KEY` → Groq (free tier)
3. Ollama running locally → Ollama (free)
4. None → offline tool routing

Force a specific mode: `LLM_PROVIDER=offline|groq|ollama|openai`
