# Claude Agents Registry

A curated set of 8 specialized system prompts ("agents") for [Claude](https://claude.ai), adapted from an earlier Grok-based registry. Each agent is a self-contained persona designed to be dropped into a [Claude Project](https://docs.claude.com/) or pasted as the opening message of a chat.

The registry is distributed as a single JSON file (`claude-agents.json`) that any application, script, or UI can consume.

---

## Why this exists

Generic chat assistants are flexible but unfocused. By committing a persona to a Claude Project's custom instructions, you get consistent, high-quality output for a specific kind of work — research, code, writing, data, visuals, orchestration, or Brazilian-market work — without re-explaining the brief every session.

This repository keeps those personas version-controlled, reviewable, and shareable.

---

## The agents

| Emoji | Name | Focus |
|---|---|---|
| 🔍 | Deep Research Agent | Multi-source verification, citation-backed synthesis |
| 🛠️ | CodeForge | Full-lifecycle software engineering inside Code Execution |
| 🎨 | VisualCraft | SVG, HTML/React UIs, diagrams, video, presentations |
| 📖 | Narrative Weaver | Long-form storytelling and content, EN & PT-BR |
| 📊 | Quant Analyst | Statistical modeling, forecasting, data viz |
| ⚙️ | Automation Orchestrator | Sequential decomposition of complex projects |
| 🇧🇷 | Brazilian Cultural Agent | PT-BR localization, business culture, regulation |
| 🧠 | Chief of Staff (Meta) | Strategic planning across the other personas |

Full descriptions, capabilities, suggested tools, example prompts, and the complete system prompt for each agent live inside `claude-agents.json`.

---

## File structure

```
.
├── claude-agents.json    # the registry (exported from the Hub artifact)
├── loader.py             # Python loader + CLI (get_agent, list_agents, search, validate)
├── LICENSE               # MIT license
├── .gitignore            # standard Python ignores
├── .github/
│   └── workflows/
│       └── validate.yml  # CI: validates the registry on every push
└── README.md             # this file
```

---

## JSON schema

`claude-agents.json` is a flat object keyed by agent ID. Each entry has the following shape:

```json
{
  "agent_id": {
    "name": "Human-readable name",
    "emoji": "🔍",
    "accent": "from-blue-500 to-sky-400",
    "ring": "ring-blue-500/30",
    "glow": "shadow-blue-500/10",
    "description": "One-sentence summary.",
    "claudeTools": [
      "web_search",
      "web_fetch",
      "Code Execution"
    ],
    "capabilities": [
      "Capability 1",
      "Capability 2"
    ],
    "examples": [
      "Example prompt 1",
      "Example prompt 2"
    ],
    "systemPrompt": "The full system prompt, ready to paste into Claude Projects."
  }
}
```

| Field | Type | Notes |
|---|---|---|
| `name` | string | Display name |
| `emoji` | string | Single emoji used as visual identifier |
| `accent`, `ring`, `glow` | string | Tailwind utility classes used by the Hub UI; safe to ignore if you don't render with Tailwind |
| `description` | string | Short one-liner shown in card views |
| `claudeTools` | string[] | Suggested Claude capabilities the persona expects to have access to |
| `capabilities` | string[] | High-level skills the agent advertises |
| `examples` | string[] | Sample prompts that play to the agent's strengths |
| `systemPrompt` | string | **The thing you actually paste into Claude.** All other fields are metadata around it. |

---

## How to use these agents

### Option A — Claude Projects (recommended)

For any persona you'll use more than once:

1. Open Claude → **Settings → Projects → New project**
2. Open `claude-agents.json`, find the agent you want, and copy its `systemPrompt` field
3. Paste it into the project's **Custom instructions** field
4. Optionally add reference files (style guides, examples, datasets) to the project's knowledge
5. Start any chat inside that project — Claude will adopt the persona automatically

### Option B — One-off paste

For occasional use, paste the `systemPrompt` as the very first message of a new chat. The persona will hold for the rest of that conversation but won't carry over to new chats.

### Option C — Programmatic (API)

If you're calling Claude through the [Anthropic API](https://docs.claude.com/en/api), pass the agent's `systemPrompt` as the `system` parameter:

```python
import json
import anthropic

with open("claude-agents.json") as f:
    agents = json.load(f)

client = anthropic.Anthropic()

resp = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    system=agents["deep_research"]["systemPrompt"],
    messages=[
        {"role": "user", "content": "Research the current state of quantum computing commercialization."}
    ],
)

print(resp.content[0].text)
```

### Option D — Loader module

A minimal Python loader (mirrors the original registry's API):

```python
import json
from typing import Any

with open("claude-agents.json") as f:
    AGENTS: dict[str, dict[str, Any]] = json.load(f)


def get_agent(agent_key: str) -> dict[str, Any]:
    """Load a specific agent by key."""
    if agent_key not in AGENTS:
        raise ValueError(
            f"Agent '{agent_key}' not found. Available: {list(AGENTS.keys())}"
        )
    return AGENTS[agent_key]


def list_agents() -> list[str]:
    """Return all available agent keys."""
    return list(AGENTS.keys())


def print_agent_summary(agent_key: str) -> None:
    """Pretty print agent information."""
    a = get_agent(agent_key)
    print(f"\n{a['emoji']} {a['name']}")
    print(f"Description: {a['description']}")
    print(f"Capabilities: {', '.join(a['capabilities'])}")
    print(f"Suggested tools: {', '.join(a['claudeTools'])}")
```

---

## Adaptation notes (Grok → Claude)

These prompts were originally written for a Grok-style environment with tools like `bash`, `write_file`, `x_keyword_search`, `browse_page`, and native image generation. They have been rewritten to target Claude's actual capabilities:

| Original (Grok) | Replacement (Claude) |
|---|---|
| `bash`, `read_file`, `write_file`, `edit_file`, `list_dir` | Code Execution + File Creation |
| `browse_page` | `web_fetch` |
| `x_keyword_search`, `x_semantic_search` | Removed — no X/Twitter access in Claude |
| `generate_image`, `edit_image` | Removed — Claude has no native raster image generation. VisualCraft routes into SVG/HTML/React Artifacts, Mermaid, ffmpeg via Code Execution, and python-pptx |
| `ffmpeg`, `pptx` skill | Code Execution (ffmpeg, python-pptx) or Claude for PowerPoint |
| "Parallel sub-agents" framing | Sequential mode-switching within one conversation (Claude does not spawn parallel agents) |
| References to "Grok ecosystem" / "Grok Imagine" | Rewritten to reference Claude features (Artifacts, Projects, Memory, Code Execution) |

Two prompts received structural revisions beyond simple tool-name swaps:

- **Automation Orchestrator** and **Chief of Staff (Meta)** were reframed to acknowledge that Claude doesn't run parallel agents. They now describe sequential checkpoints inside a single conversation, and recommend Claude Projects for persistence across sessions.
- **Deep Research Agent** was updated to explicitly invoke Claude's built-in citation system and the standard copyright limits (paraphrase by default, quotes under 15 words, one quote per source).

---

## Updating the registry

The canonical authoring environment for this file is the **Claude Agent Hub** artifact (a React UI for browsing, copying, and exporting the agents). To update:

1. Open the Hub artifact in a Claude conversation
2. Make edits there (or regenerate the JSON from an updated source)
3. Click **Export JSON** to download a fresh `claude-agents.json`
4. Commit the new file to this repository

If you prefer to edit the JSON directly, make sure to preserve the schema above. All `systemPrompt` values are multi-line strings — keep newlines escaped (`\n`) or use a JSON editor that handles them cleanly.

---

## Contributing

Pull requests welcome. Suggested directions:

- Additional personas (legal, healthcare, education, specific industries)
- Better example prompts drawn from real use
- Translations of the `description`, `capabilities`, and `examples` fields into other languages (the registry currently stores them in English; only the Hub UI is bilingual)
- Loaders for other languages (TypeScript, Go, Rust)

When adding an agent, please include all schema fields and write the `systemPrompt` with the same Grok→Claude discipline applied to the existing set: reference real Claude capabilities, acknowledge limitations honestly, and frame multi-step work as sequential.

---

## License

Released under the **MIT License** — see [LICENSE](./LICENSE) for the full text. You can use, modify, and redistribute these prompts freely; attribution is appreciated but not required.

---

## Acknowledgements

- Original registry concept and agent designs by the repository author
- Adapted for Claude in conversation with [Claude](https://claude.ai) (Anthropic)
