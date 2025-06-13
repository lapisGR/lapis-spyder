# HUD SDK Documentation

- [Quickstart](quickstart.md): This comprehensive guide provides a foundational introduction to the HUD SDK. It covers essential steps from installation and API key configuration to defining and running your first tasks.
  - [Installation](quickstart.md#installation): Learn how to install the HUD SDK using pip and set up your development environment.
  - [API Key Configuration](quickstart.md#api-key-configuration): Configure your HUD API key to authenticate your SDK requests.
  - [Your First Task](quickstart.md#defining-your-first-task): Create and run your first task to understand the basic workflow.
  - [Browser Interaction](quickstart.md#browser-interaction-with-agents): Learn how to interact with browsers using agents and the Chrome DevTools Protocol (CDP).
  - [Running Tasks](quickstart.md#running-tasks): Execute tasks and understand the different execution modes.
  - [TaskSet Evaluation](quickstart.md#evaluating-agents-with-tasksets): Evaluate agent performance using predefined TaskSets.
  - [MCP Telemetry](quickstart.md#exploring-mcp-telemetry): Monitor and debug agent behavior with Model Context Protocol telemetry.
  - [Common Task Examples](quickstart.md#common-tasks): Explore ready-to-use task patterns for common scenarios.

- [Task Creation](task-creation.md): Learn how to create and configure tasks for browser-based agent evaluation.
  - [Task Basics](task-creation.md#tasks): Understand the fundamental components of a task in the HUD SDK.
  - [Task Configuration](task-creation.md#task-configuration): Configure task parameters, expected outcomes, and evaluation criteria.
  - [TaskSets](task-creation.md#tasksets): Organize multiple tasks into coherent evaluation sets.
  - [Evaluation Metrics](task-creation.md#evaluation-metrics): Define and implement custom evaluation metrics for your tasks.
  - [Browser Control](task-creation.md#browser-control): Master browser automation techniques for complex task scenarios.
  - [Agent Instructions](task-creation.md#agent-instructions): Write effective instructions for agents to complete tasks.
  - [Success Criteria](task-creation.md#success-criteria): Define clear success conditions for task completion.

## Key Concepts

- **Agents**: Autonomous programs that interact with web browsers to complete tasks. They can be AI-powered or rule-based systems that navigate, interact with, and extract information from web pages.

- **Tasks**: Specific objectives that agents must complete, such as filling out forms, extracting data, or navigating through websites. Each task includes instructions, expected outcomes, and evaluation criteria.

- **TaskSets**: Collections of related tasks designed to comprehensively evaluate agent capabilities. They provide standardized benchmarks for comparing different agent implementations.

- **MCP Telemetry**: Model Context Protocol telemetry provides real-time insights into agent behavior, decision-making processes, and performance metrics during task execution.

- **Browser Automation**: The SDK leverages Chrome DevTools Protocol (CDP) for precise browser control, enabling agents to perform complex interactions like clicking, typing, scrolling, and handling dynamic content.

## Common Patterns

- **Question Answering**: Tasks where agents extract information from web pages to answer specific questions.
- **Form Interaction**: Tasks involving filling out web forms with appropriate data and submitting them.
- **Navigation Tasks**: Tasks requiring agents to navigate through multi-page workflows or complex site structures.
- **Data Extraction**: Tasks focused on scraping and structuring information from web pages.
- **Interactive Workflows**: Tasks that require multiple steps of interaction with dynamic web applications.

## API Reference

- **Core Classes**:
  - `HUD`: Main class for SDK initialization and configuration
  - `Task`: Base class for defining evaluation tasks
  - `TaskSet`: Container for organizing multiple tasks
  - `Agent`: Interface for agent implementations
  
- **Browser Control**:
  - `Browser`: High-level browser automation interface
  - `Page`: Page-level interaction methods
  - `Element`: Element selection and manipulation

- **Evaluation**:
  - `Evaluator`: Task evaluation engine
  - `Metrics`: Performance metric definitions
  - `Results`: Evaluation result structures

## Getting Help

- **Discord Community**: Join our Discord server for real-time support and discussions
- **GitHub Issues**: Report bugs or request features on our GitHub repository
- **API Documentation**: Detailed reference documentation at docs.hud.so/api
- **Examples Repository**: Browse working examples at github.com/hud-ai/sdk-examples