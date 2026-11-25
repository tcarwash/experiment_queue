---
name: experiment-submission
description: Use when a user wants an agent to design, prepare, validate and submit a pinned distributed research experiment through GitHub Issues.
---

Read `AGENTS.md` and `docs/agents/EXPERIMENT_AUTHORING.md`, then read the target research repository's own `AGENTS.md`. Put reproducible scripts and fixtures in a pushed Git commit, pin the full SHA, select the minimum required capability and approved image/adapter, write the single fenced JSON manifest and validate it. Use `gh issue create` only when authorized. Mark the issue `experiment-ready` only when source, hardware and image eligibility have been checked or explicitly approved. Return the issue URL and expected evidence; do not claim the experiment has run unless it has.
