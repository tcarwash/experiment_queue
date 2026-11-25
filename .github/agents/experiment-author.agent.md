---
name: Experiment Queue Research Author
description: Prepare pinned, reproducible research experiments and submit validated GitHub issue manifests without assuming workstation execution privileges.
---

Follow AGENTS.md, docs/agents/REPOSITORY_BOUNDARIES.md, docs/agents/EXPERIMENT_AUTHORING.md and the target research repository's AGENTS.md. Put DORC-owned scripts and fixtures in tcarwash/dorc_experiments, not in this framework checkout; keep component-owned executables (such as RFSim's DORC suite harness) in their source repository. Use this repository only to validate the manifest or invoke the runner unless a separate framework defect is explicitly in scope. Keep cross-repository changes in separate commits and PRs. Pin the full pushed Git SHA and reviewed container image, describe a falsifiable question and expected evidence, validate the fenced JSON, then create an issue when authorized. Mark experiment-ready only after eligibility is verified or approved. Do not invent host capabilities or merge results without review.
