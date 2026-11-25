## Research question

What are we trying to establish? State the hypothesis, controls, and how a
negative result will be recognized. See docs/agents/EXPERIMENT_AUTHORING.md.

## Procedure and expected evidence

Prepare and push the executable source commit before filing. Replace the
full-length source revision and immutable image ID placeholders. CPU container
workloads are the default; `scripted` execution is unsandboxed and disallowed
by default. A valid result writes report.md under EXPERIMENT_OUTPUT even when
the hypothesis is disproved.

```json
{
  "schema": "experiment/v1",
  "execution": "container",
  "source": "https://github.com/OWNER/PROJECT.git",
  "revision": "0000000000000000000000000000000000000000",
  "image": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "command": ["/bin/sh", "experiments/example.sh"],
  "capabilities": ["compute.cpu"],
  "timeout": 300
}
```

Only add experiment-ready after the exact image, source, capabilities and
runtime have been approved by an actual contributor and the issue is valid.
