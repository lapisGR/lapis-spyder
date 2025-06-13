## Advanced Patterns



### ​Environment-Specific Evaluation


```python
# Browser-specific evaluation
if task.gym == "hud-browser":
    evaluate=("element_exists", ".success-indicator")
# Response-only evaluation
if task.gym == "qa":
    evaluate=("response_includes", "expected_answer")
```


### ​Dynamic Task Generation


```python
def create_search_task(query, expected_result):
    return Task(
        prompt=f"Search for '{query}' and find information about it",
        gym="hud-browser",
        setup=("goto", "google.com"),
        evaluate=("response_includes", expected_result)
    )
task = create_search_task("artificial intelligence", "machine learning")
```