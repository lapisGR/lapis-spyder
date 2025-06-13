# Job - hud SDK

**URL**: https://docs.hud.so/concepts/job

**Code Examples**: 3

---

Job - hud SDK# (#job)Job

A `Job` groups related [Environment](https://docs.hud.so/concepts/environment) runs ([Trajectories](https://docs.hud.so/concepts/trajectory)) for organization and analysis.

## (#overview)Overview

Jobs help organize evaluation data, useful for:

- Grouping runs for a specific agent version or experiment.
- Running multiple trials of the same [Task](https://docs.hud.so/concepts/task).
- Comparing different agent configurations.
- Viewing aggregated results and videos on the [HUD platform](https://app.hud.so/jobs).

## (#creating-jobs)Creating Jobs

### (#1-the-%40register-job-decorator-recommended)1. The `@register_job` Decorator (Recommended)

Decorate an `async` function. A new Job is created per function call, and any environments created within using `hud.gym.make()` are automatically linked.

```
from hud import gym, register_job
from hud.task import Task
from hud.agent import OperatorAgent # Example agent

@register_job(name="my-evaluation-run", metadata={"agent_version": "1.1"})
async def run_evaluation():
    task = Task(prompt="Example", gym="hud-browser")
    env = await gym.make(task) # Linked to "my-evaluation-run" job

    agent = OperatorAgent(environment="browser")
    # ... interaction loop ...

    await env.close() # Trajectory saved to the job

# await run_evaluation()

```

- **`name` (str):** Job name on the HUD platform.
- **`metadata` (dict | None):** Optional data for tracking.

### (#2-manual-creation-create-job)2. Manual Creation (`create_job`)

Create a `Job` object manually and pass it to `gym.make()`.

```
from hud import gym, create_job
from hud.task import Task

async def manual_job_example():
    my_job = await create_job(name="manual-job")
    task = Task(prompt="Manual", gym="hud-browser")
    # Explicitly link environment to the created job

    env = await gym.make(task, job=my_job)
    # ... interaction loop ...

    await env.close()

# await manual_job_example()

```

## (#accessing-job-data)Accessing Job Data

Load a `Job` by its ID to retrieve its details and associated [Trajectories](https://docs.hud.so/concepts/trajectory).

```
from hud import load_job

async def analyze_job(job_id: str):
    job = await load_job(job_id)
    print(f"Job: {job.name}, Metadata: {job.metadata}")

    # Load associated trajectories

    trajectories = await job.load_trajectories()
    print(f"Found {len(trajectories)} trajectories.")
    for traj in trajectories:
        print(f" - Trajectory ID: {traj.id}, Reward: {traj.reward}")
        # Video links available on the HUD platform job page

```

### (#job-properties)Job Properties

- `id` (str)
- `name` (str)
- `metadata` (dict | None)
- `created_at` (datetime)
- `status` (str)

## (#best-practices)Best Practices

- Use `@register_job` for most scripts.
- Use descriptive names and metadata.
- Create separate jobs for distinct experiments.

## (#related-concepts)Related Concepts

- [Environment](https://docs.hud.so/concepts/environment): Runs are linked to Jobs.
- [Trajectory](https://docs.hud.so/concepts/trajectory): Recordings grouped by Job; accessed via `job.load_trajectories()`.
- [Task](https://docs.hud.so/concepts/task): Defines the scenario for runs within a Job.
[Environment](https://docs.hud.so/concepts/environment)[Tasks and TaskSets](https://docs.hud.so/concepts/task)