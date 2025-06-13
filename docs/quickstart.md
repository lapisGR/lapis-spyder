Quickstart - hud SDKGetting Started# Quickstart

## [​](https://docs.hud.so/quickstart#1-installation)1. Installation

Install the hud SDK:

Copy
See [Installation](https://docs.hud.so/installation) for more details on development setup.

## [​](https://docs.hud.so/quickstart#2-api-key-setup)2. API Key Setup

Set your API keys in a `.env` file (get your HUD API key from [app.hud.so](https://app.hud.so)):

Copy

## [​](https://docs.hud.so/quickstart#3-your-first-task)3. Your First Task

Copy
Each gym (`hud-browser`, `OSWorld-Ubuntu`, custom) has it’s own set of setup and evaluate funcitons, and you can define your own.
See [setup](https://docs.hud.so/environments/browser#setup-functions-initial-state) and [evalutors](https://docs.hud.so/environments/browser#evaluation-functions) for more info on available functions.

### [​](https://docs.hud.so/quickstart#manual-agent-loop)Manual Agent Loop

Copy

## [​](https://docs.hud.so/quickstart#4-browser-interaction-patterns)4. Browser Interaction Patterns

### [​](https://docs.hud.so/quickstart#live-streaming)Live Streaming

Copy

### [​](https://docs.hud.so/quickstart#browser-use-integration-through-cdp)Browser Use Integration through CDP

Copy

## [​](https://docs.hud.so/quickstart#5-taskset-evaluation)5. TaskSet Evaluation

Evaluate your agent on pre-built TaskSets:

Copy

## [​](https://docs.hud.so/quickstart#6-mcp-telemetry-integration)6. MCP Telemetry Integration

HUD automatically captures MCP tool calls for debugging:

Copy
**What’s Captured**:

- Tool invocations and responses
- Error states and retries
- Performance data
- Request/response payloads

## [​](https://docs.hud.so/quickstart#7-common-task-patterns)7. Common Task Patterns

### [​](https://docs.hud.so/quickstart#question-answering)Question Answering

Copy

### [​](https://docs.hud.so/quickstart#form-interaction)Form Interaction

Copy

### [​](https://docs.hud.so/quickstart#spreadsheet-tasks)Spreadsheet Tasks

Copy

### [​](https://docs.hud.so/quickstart#response-only-tasks-no-browser)Response-Only Tasks (No Browser)

Copy

## [​](https://docs.hud.so/quickstart#next-steps)Next Steps

- **[Task Creation Guide](https://docs.hud.so/task-creation)**: Deep dive into building custom evaluation scenarios
- **[Custom Environments](https://docs.hud.so/environment-creation)**: Create Docker-based environments for your applications
- **[Browser Environment](https://docs.hud.so/environments/browser)**: Learn browser-specific features
- **[Examples](https://docs.hud.so/examples)**: Browse runnable notebooks

---

## [​](https://docs.hud.so/quickstart#custom-installation-%26-setup)Custom Installation & Setup

If you haven’t installed the SDK yet, here’s how:

### [​](https://docs.hud.so/quickstart#standard-installation)Standard Installation

Install the HUD SDK using pip:

Copy

### [​](https://docs.hud.so/quickstart#requirements)Requirements

- **Python:** 3.10 or higher
- **API Keys:**
	- `HUD_API_KEY` (required for platform features like job/trace uploading, loading remote TaskSets).
	- `OPENAI_API_KEY` (optional, required if using `OperatorAgent` or other OpenAI-based agents).
	- `ANTHROPIC_API_KEY` (optional, required if using `ClaudeAgent` or other Anthropic-based agents).

### [​](https://docs.hud.so/quickstart#api-key-configuration)API Key Configuration

The SDK automatically loads API keys from environment variables or a `.env` file located in your project’s root directory.

Create a `.env` file in your project root:

Copy
Alternatively, export them as environment variables in your shell.

### [​](https://docs.hud.so/quickstart#development-installation-for-contributors)Development Installation (for Contributors)

If you plan to contribute to the SDK or need an editable install:

Copy
With the SDK installed and API keys configured, you’re ready to explore all examples and build your own agent evaluations!

[Tasks](https://docs.hud.so/task-creation)[github](https://github.com/hud-evals/hud-sdk)[website](https://hud.so)[Powered by Mintlify](https://mintlify.com/preview-request?utm_campaign=poweredBy&utm_medium=referral&utm_source=docs.hud.so)
