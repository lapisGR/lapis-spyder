# Tasks and TaskSets - hud SDK

**URL**: https://docs.hud.so/concepts/task

**Code Examples**: 4

---

Tasks and TaskSets - hud SDK# (#tasks-and-tasksets)Tasks and TaskSets

Tasks define *what* an [Agent](https://docs.hud.so/concepts/agent) should do in an [Environment](https://docs.hud.so/concepts/environment), including the goal, initial setup steps, and how to evaluate success. [TaskSets](#taskset) are collections of related tasks.

## (#task)Task

A `Task` object provides the configuration for a specific scenario.

### (#key-attributes)Key Attributes

- **`prompt` (str):** The primary instruction given to the agent.
- **`gym` (str | `CustomGym` | None):** Specifies the type of [Environment](https://docs.hud.so/concepts/environment) needed. Used by `hud.gym.make()`.
- **`setup` (`FunctionConfigs` | None):** Defines actions executed *before* the agent starts. See [Setup Configuration](#setup-configuration).
- **`evaluate` (`FunctionConfigs` | None):** Defines how to check if the agent succeeded *after* interaction. See [Evaluation Configuration](#evaluation-configuration).
- **`id` (str | None):** Optional identifier.
- **`metadata` (dict | None):** Optional dictionary for extra information.
- **`config` (dict | None):** Optional dictionary, primarily for remote execution.

### (#creating-a-task)Creating a Task

```
from hud.task import Task

task = Task(
    prompt="Log in to example.com with username 'test'",
    gym="hud-browser", # Request a browser environment

    setup=[ # Actions run by gym.make(task)

        ("goto", "https://example.com/login")
    ],
    evaluate={ # Logic run by env.evaluate()

        "function": "page_contains", 
        "args": ["test"]
    }
)
```

### (#configuration-styles-setup-and-evaluate)Configuration Styles (`setup` and `evaluate`)

Both `setup` and `evaluate` accept configurations defining function calls within the environment’s controller, using flexible formats (`FunctionConfigs`):

1. **String:** `"browser.maximize"`
2. **Tuple:** `("goto", "https://google.com")`
3. **Dictionary:** `{"function": "wait_for_element", "args": ["#submit"]}`
4. **List:** `[("goto", "page1"), ("click", "#next")]` (Executed sequentially)

### (#setup-configuration-setup)Setup Configuration (`setup`)

- **Purpose:** Establishes a consistent starting state before the agent interacts.
- **Execution:** Automatically run by `hud.gym.make(task)`. Can be run manually via `env._setup()`.
- **Examples:** Navigating to a URL, logging in, preparing files.

### (#evaluation-configuration-evaluate)Evaluation Configuration (`evaluate`)

- **Purpose:** Determines task success after the agent finishes.
- **Execution:** Triggered by `await env.evaluate()`.
- **Result:** The return value of `env.evaluate()`, often a reward score (e.g., `1.0` or `0.0`). This is stored in the `reward` field of the [Trajectory](https://docs.hud.so/concepts/trajectory) if linked to a [Job](https://docs.hud.so/concepts/job).
- **Examples:**
	- Interactive: `("contains_text", "Success!")`, `("file_exists", "/path/to/output.txt")`. These typically call functions *within* the active environment controller.
	- QA: `("response_includes", "Paris")`. These functions often check the text stored in `env.final_response` (which comes from the agent’s `ResponseAction`).
- **Note:** Check specific environment or evaluation service documentation for available functions.

## (#taskset)TaskSet

A `TaskSet` is a list of related `Task` objects, useful for benchmarks.

### (#key-attributes-2)Key Attributes

- **`tasks` (list[`Task`]):** The list of tasks.
- **`id` (str | None):** Optional identifier.
- **`description` (str | None):** Optional description.

### (#loading-a-taskset)Loading a TaskSet

Load predefined sets from the HUD platform:

```
from hud import load_taskset

taskset = await load_taskset("OSWorld-Ubuntu")
print(f"Number of tasks: {len(taskset)}") # TaskSet acts like a list

first_task = taskset[0]
```

Currently supported TaskSets available via `load_taskset` include OSWorld, GAIA, and WebVoyager subsets.

### (#creating-a-taskset-manually)Creating a TaskSet Manually

```
from hud.task import Task
from hud.taskset import TaskSet

task1 = Task(...); task2 = Task(...)
my_taskset = TaskSet(tasks=[task1, task2], description="My set")
```

## (#related-concepts)Related Concepts

- [Environment](https://docs.hud.so/concepts/environment): Where Tasks are executed and evaluated.
- [Agent](https://docs.hud.so/concepts/agent): Aims to complete the Task `prompt`.
- [Job](https://docs.hud.so/concepts/job): Groups runs of different Tasks.
- [Trajectory](https://docs.hud.so/concepts/trajectory): Records the execution of a Task.

### (#defining-question-answering-qa-tasks)Defining Question-Answering (QA) Tasks

While HUD excels at interactive tasks, you can also define tasks that are primarily question-answering. The key differences are:

- **`gym`:** You might still use an existing environment type like `"hud-browser"` if you want the QA to happen *within* that context (e.g., asking the agent to answer based on a webpage). For pure QA without environment interaction, a future specific `"qa"` gym type might be introduced, but currently, you’d use an existing type.
- **`prompt`:** Contains the question for the agent.
- **`setup`:** Often minimal or unnecessary for pure QA.
- **`evaluate`:** Defines how to check the agent’s final text answer. This typically involves calling a specific evaluation function that compares the agent’s final submitted response (see `ResponseAction` in [CLA Details](https://docs.hud.so/advanced/cla-details)) against expected criteria. The `env.final_response` attribute holds the text submitted by the agent via `ResponseAction`.
- **`target`:** (Recommended) Store the ground truth answer in the `metadata` or potentially a dedicated `target` field for clarity during evaluation function design.

```
from hud.task import Task

qa_task = Task(
    prompt="What is the powerhouse of the cell?",
    gym="hud-browser", # Or potentially a future "qa" type

    # No complex setup needed for pure QA

    setup=(),
    # Evaluation checks the agent's final submitted text response

    evaluate=("response_includes", "mitochondria"), # Assumes a function checking env.final_response

)
```

The [Agent](https://docs.hud.so/concepts/agent) handling such a task should recognize it doesn’t need complex interaction and output a `ResponseAction` containing the final answer. The `env.evaluate()` call then triggers the specified check (like `response_includes`) against the stored response.

### (#configuration-styles-setup-and-evaluate-2)Configuration Styles (`setup` and `evaluate`)

[Job](https://docs.hud.so/concepts/job)[Trajectory](https://docs.hud.so/concepts/trajectory)