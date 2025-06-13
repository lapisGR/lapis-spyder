Tasks - hud SDKGetting Started# Tasks

Design, build, and share evaluation scenarios for browser-based agents

# [​](https://docs.hud.so/task-creation#creating-tasks-%26-tasksets)Creating Tasks & TaskSets

Tasks define what browser-based agents should accomplish and how success is measured. TaskSets group these tasks for benchmarking and sharing.

## [​](https://docs.hud.so/task-creation#core-task-workflow)Core Task Workflow

1. **Define Task**: Specify prompt, setup, and evaluation criteria for a specific environment.
2. **Test Locally**: Use `gym.make(task)` and `env.run(agent)` to iterate on your task.
3. **(Optional) Group into TaskSet**: Collect related tasks for benchmarking or organized evaluation.
4. **(Optional) Upload TaskSet**: Share your TaskSet on the HUD platform.

## [​](https://docs.hud.so/task-creation#task-structure)Task Structure

While tasks can be designed for various environments, this guide focuses on tasks for the `hud-browser`.
For creating tasks that operate in specialized Docker environments (e.g., desktop applications, custom web apps), please see the [Environment Creation & Contribution Guide](https://docs.hud.so/environment-creation).

Copy

## [​](https://docs.hud.so/task-creation#setup-functions-for-hud-browser)Setup Functions (for `hud-browser`)

| Function | Description |
| --- | --- |
| `goto(url)` | Navigates to a URL. |
| `load_html_content(html)` | Loads static HTML content into the browser. |
| `sheets_from_xlsx(url)` | Downloads XLSX, converts to Google Sheet, and navigates to it. |

For a detailed list of all setup functions available in the `hud-browser` environment and their usage examples, please see the **[Browser Environment Setup Functions Documentation](https://docs.hud.so/environments/browser#setup-functions)**.

## [​](https://docs.hud.so/task-creation#evaluate-functions-verifying-task-success)Evaluate Functions (Verifying Task Success)

Evaluate functions are called by `env.evaluate()` *after* the agent has completed its interactions (or reached a step limit) to determine if the task objectives were met.

For `hud-browser` tasks, evaluation functions commonly check page content, URL, browser state, or the agent’s actions and final response:

| Category | Common Functions |
| --- | --- |
| Content | `page_contains`, `element_exists`, `text_matches` |
| URL/Navigation | `url_contains`, `url_match` |
| Browser State | `cookie_exists` |
| Agent Response | `response_includes` |
| Action History | `selector_history`, `verify_type_action`, `history_length`, `raw_last_action_is` |
| Spreadsheets | `sheets_cell_values` |

For a detailed list of all evaluation functions available in the `hud-browser` environment, their parameters, and usage examples, please see the **[Browser Environment Evaluate Functions Documentation](https://docs.hud.so/environments/browser#evaluate-functions)**.

## [​](https://docs.hud.so/task-creation#taskset-creation-%26-management)TaskSet Creation & Management

TaskSets are collections of related `Task` objects, useful for running benchmarks, organizing evaluations, or sharing common scenarios.

### [​](https://docs.hud.so/task-creation#creating-a-taskset)Creating a TaskSet

Copy

### [​](https://docs.hud.so/task-creation#uploading-%26-publishing-tasksets)Uploading & Publishing TaskSets

Once created, you can upload your TaskSet to the HUD platform to make it available for yourself, your team, or the public.

Copy

### [​](https://docs.hud.so/task-creation#publishing-and-sharing)Publishing and Sharing

Once uploaded, TaskSets can be:

- **Private**: Visible only to you by default.
- **Public**: Optionally publish to the wider HUD community.
- **Shared with Team**: (Coming Soon) Share within your HUD organization.

Uploaded TaskSets are managed at [app.hud.so/evalsets](https://app.hud.so/evalsets).

## [​](https://docs.hud.so/task-creation#pre-built-tasksets)Pre-built TaskSets

Load and run existing benchmarks:

Copy
**Available TaskSets on hud:**

- **WebVoyager**: Web navigation and complex interaction.
- **Mind2Web**: Tasks on real-world websites.
- **GAIA**: Challenging reasoning and multi-hop QA.
- **OSWorld-Ubuntu**: Desktop environment tasks (requires custom OS environments).
- **hud-samples**: Introductory examples to get started.

## [​](https://docs.hud.so/task-creation#mcp-telemetry-with-tasks)MCP Telemetry with Tasks

When using MCP-enabled agents, HUD automatically traces tool calls made during task execution if wrapped in `hud.trace()`:

Copy

## [​](https://docs.hud.so/task-creation#best-practices-for-task-design)Best Practices for Task Design

1. **Clear Prompts**: Ensure agent understands the goal and success criteria.
2. **Atomic Tasks**: Break down complex goals into smaller, testable tasks.
3. **Robust Setup**: Create consistent starting states.
4. **Comprehensive Evaluation**: Use multiple evaluation functions to validate success.
5. **Iterate**: Test and refine tasks, especially evaluation logic.

## [​](https://docs.hud.so/task-creation#advanced-patterns)Advanced Patterns

### [​](https://docs.hud.so/task-creation#environment-specific-evaluation)Environment-Specific Evaluation

Copy

### [​](https://docs.hud.so/task-creation#dynamic-task-generation)Dynamic Task Generation

Copy

## [​](https://docs.hud.so/task-creation#related-guides)Related Guides

- **[Browser Environment](https://docs.hud.so/environments/browser)**: Detailed guide on using `hud-browser`, including all its setup and evaluation functions.
- **[Environment Creation & Contribution](https://docs.hud.so/environment-creation)**: For tasks requiring specialized Docker-based environments.
- **[Quickstart](https://docs.hud.so/quickstart)**: Introductory examples and common usage patterns.
- **[API Reference](https://docs.hud.so/api-reference)**: Comprehensive details for all SDK modules and classes.
[Quickstart](https://docs.hud.so/quickstart)[Environments](https://docs.hud.so/environment-creation)[github](https://github.com/hud-evals/hud-sdk)[website](https://hud.so)[Powered by Mintlify](https://mintlify.com/preview-request?utm_campaign=poweredBy&utm_medium=referral&utm_source=docs.hud.so)
