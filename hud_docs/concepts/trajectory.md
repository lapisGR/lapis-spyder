# Trajectory - hud SDK

**URL**: https://docs.hud.so/concepts/trajectory

**Code Examples**: 2

---

Trajectory - hud SDK# (#trajectory)Trajectory

A `Trajectory` represents the detailed recording of a single run of an [Agent](https://docs.hud.so/concepts/agent) within an [Environment](https://docs.hud.so/concepts/environment) for a specific [Task](https://docs.hud.so/concepts/task).

## (#overview)Overview

Trajectories capture the step-by-step history of an agent’s interaction, useful for analysis, debugging, and visualization.

They are automatically generated and associated with a [Job](https://docs.hud.so/concepts/job) when `env.close()` is called on a linked environment.

## (#accessing-trajectories)Accessing Trajectories

The primary way to access trajectories is through a [Job](https://docs.hud.so/concepts/job) object using `job.load_trajectories()`:

```
from hud import load_job

async def analyze_job_trajectories(job_id: str):
    job = await load_job(job_id)
    trajectories = await job.load_trajectories()

    for i, traj in enumerate(trajectories):
        print(f"--- Trajectory {i+1} (ID: {traj.id}) ---")
        print(f"  Reward: {traj.reward}")
        print(f"  Number of steps: {len(traj.trajectory)}") # Access the list of steps

        if traj.error:
            print(f"  Error: {traj.error}")

        # You can iterate through individual steps if needed

        # for step_index, step_data in enumerate(traj.trajectory):

        #    print(f"    Step {step_index}: Actions: {step_data.actions}")

        #    print(f"    Step {step_index}: Obs Text: {step_data.observation_text}")

        #    print(f"    Step {step_index}: Obs Image URL: {step_data.observation_url}")

```

## (#key-properties)Key Properties

A `Trajectory` object contains:

- `id` (str): Unique ID for this run.
- `reward` (float | None): The final evaluation score from the [Task](https://docs.hud.so/concepts/task)’s `evaluate` logic.
- `logs` (str | None): Captured logs.
- `error` (str | None): Error message if the run failed.
- `trajectory` (list[`TrajectoryStep`]): List of individual steps.

Each `TrajectoryStep` contains:

- `observation_url` (str | None): URL to the step’s screenshot.
- `observation_text` (str | None): Text observed in the step.
- `actions` (list[dict]): Agent action(s) leading to this step’s observation.
- `start_timestamp` / `end_timestamp` (str | None): Step timing.

## (#visualization)Visualization

- **HUD Platform:** The [Jobs page](https://app.hud.so/jobs) offers the best visualization, including videos.
- **Jupyter:** The `trajectory.display()` method provides basic step-by-step rendering.

```

# In Jupyter:

# traj.display()

```

## (#related-concepts)Related Concepts

- [Job](https://docs.hud.so/concepts/job): How trajectories are grouped and accessed.
- [Environment](https://docs.hud.so/concepts/environment): Generates the trajectory data during a run.
- [Task](https://docs.hud.so/concepts/task): Defines the scenario and evaluation logic recorded.
[Tasks and TaskSets](https://docs.hud.so/concepts/task)[Browser](https://docs.hud.so/environments/browser)