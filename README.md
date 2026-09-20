# 🤖 Autonomous AI Agent — Research & Intelligence Engine

A production-grade, stateful multi-agent system built with **LangGraph**, **Google Gemini**, **Tavily**, and **FastAPI**. It transforms high-level goals into multi-step execution plans, executes targeted web research, self-reflects via an Evaluator/Critic gate, and adaptively re-plans when quality criteria are not met.

---

## 🏛️ System Architecture

```text
                        ┌────────────────────────┐
                        │       User Goal        │
                        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌────────────────────────┐
                        │     1. Planner         │
                        │ (Goal Decomposition)   │
                        └───────────┬────────────┘
                                    │
                                    ▼
            ┌─────────► ┌────────────────────────┐
            │           │     2. Researcher      │ ◄───┐
            │           │ (Search & Fact Extr.)  │     │ (Next task in plan)
            │           └───────────┬────────────┘ ────┘
            │                       │ (All tasks completed)
            │                       ▼
            │           ┌────────────────────────┐
  (Re-plan  │           │      3. Evaluator      │
   Loop)    │           │ (Self-Reflection Gate) │
            │           └───────────┬────────────┘
            │                       │
     ┌──────┴──────┐          ┌─────┴─────┐
     │  4. Re-Plan │          │  Passed?  │
     │  (Correct)  │ ◄── No ──┤ (Score >= │
     └─────────────┘          │   0.75)   │
                              └─────┬─────┘
                                    │ Yes
                                    ▼
                        ┌────────────────────────┐
                        │     5. Synthesizer     │
                        │ (Executive Report Gen) │
                        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌────────────────────────┐
                        │  Final Report Output   │
                        └────────────────────────┘
```

---

## ✨ Key Features

- **Agentic Loop with Self-Correction**: Implements `Plan → Execute → Observe → Evaluate → Re-Plan`.
- **Configurable Provider Swapping**: Switch between **Google Gemini**, **OpenAI**, **Anthropic**, and local **Ollama** via `.env` without modifying code.
- **Configurable Search Tooling**: Defaults to **Tavily**, with seamless fallback or swap to **DuckDuckGo** (zero-key) or deterministic **Mock** search.
- **Real-Time Telemetry & WebSockets**: Streams intermediate thoughts, tool calls, and node state updates live to clients.
- **Interactive Web Dashboard**: Built-in visual interface at `http://localhost:8000` to monitor the agent state machine live.
- **Deterministic Guardrails**: Pydantic structured outputs and configurable retry budgets (`MAX_RETRY_LOOPS`) to prevent infinite execution cycles.

---

## 📁 Repository Structure

```text
MyAIProject/
├── pyproject.toml              # Project dependencies and build configuration
├── .env.example                # Template for environment variables and API keys
├── .env                        # Active environment configuration
├── app/
│   ├── main.py                 # FastAPI application & server entrypoint
│   ├── config.py               # Pydantic Settings configuration
│   ├── core/
│   │   └── llm.py              # LLM provider factory (Gemini, OpenAI, Anthropic, Ollama)
│   ├── tools/
│   │   └── search.py           # Web search tool (Tavily, DuckDuckGo, Mock)
│   ├── graph/
│   │   ├── state.py            # TypedDict state schema & Pydantic models
│   │   ├── workflow.py         # LangGraph StateGraph & conditional routing edges
│   │   └── nodes/
│   │       ├── planner.py      # Decomposes goal into subtasks
│   │       ├── researcher.py   # Executes searches & synthesizes findings
│   │       ├── evaluator.py    # Self-reflection critic & score assessment
│   │       ├── replan.py       # Corrective task injection upon failure
│   │       └── synthesizer.py  # Final markdown report compiler
│   ├── api/
│   │   ├── routes.py           # REST endpoints (/api/health, /api/agent/run)
│   │   └── websocket.py        # Live WebSocket event streaming (/ws/agent)
│   └── static/
│       └── index.html          # Interactive agent monitoring UI
└── tests/
    └── test_agent.py           # Unit tests for routing and tool execution
```

---

## 🚀 Quickstart

### 1. Configure Environment Variables

Edit `.env` (copied from `.env.example`) and insert your API keys:

```bash
# LLM Settings
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here

# Search Tool Settings
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: Try DuckDuckGo search (requires no API key)
# SEARCH_PROVIDER=duckduckgo
```

### 2. Run the Service

Launch the FastAPI application with `uv`:

```bash
uv run python -m app.main
```

The server will start on **`http://localhost:8000`**.

### 3. Access the Dashboard & API

- **Web Dashboard**: Open [http://localhost:8000](http://localhost:8000) in your browser to launch goals and watch the agent work in real-time.
- **Interactive Swagger Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs) for the REST OpenAPI specifications.
- **Health & Provider Check**: `GET /api/health`

### 4. Run Automated Tests

```bash
uv run pytest
```

---

## 🔄 Swapping Providers

To swap LLMs or Search providers, simply update your `.env`:

| Provider | Setting | Required Keys |
| :--- | :--- | :--- |
| **Gemini** (Default) | `LLM_PROVIDER=gemini` | `GEMINI_API_KEY` |
| **OpenAI** | `LLM_PROVIDER=openai` | `OPENAI_API_KEY` |
| **Anthropic** | `LLM_PROVIDER=anthropic` | `ANTHROPIC_API_KEY` |
| **Ollama** | `LLM_PROVIDER=ollama` | `OLLAMA_BASE_URL` |
| **Tavily** (Default) | `SEARCH_PROVIDER=tavily` | `TAVILY_API_KEY` |
| **DuckDuckGo** | `SEARCH_PROVIDER=duckduckgo` | None (Free / No key) |
| **Mock** | `SEARCH_PROVIDER=mock` | None (Offline simulation) |
