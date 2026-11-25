## Research question

What are we trying to establish?

## Procedure and expected evidence

A successful execution must write report.md to EXPERIMENT_OUTPUT, even if the hypothesis is disproven.

```json
{
  "schema": "experiment/v1",
  "execution": "scripted",
  "source": "https://github.com/OWNER/PROJECT.git",
  "revision": "0000000000000000000000000000000000000000",
  "command": ["python3", "experiments/example.py"],
  "capabilities": ["compute.cpu"],
  "timeout": 300
}
```
