# Experiment Runner

A contributor-controlled, GitHub-backed distributed research queue. Initial prototype; do not run untrusted code.

## Quick start

Create a private research repository with a default branch and label `experiment-ready`. Clone it locally, authenticate Git and gh, and copy templates/policy.json to policy.json. Explicitly approve native execution and trusted source URLs only on a dedicated account or machine. Native execution is NOT sandboxed: the child can access the user's files, network and credentials despite the reduced environment.

Use Python 3.11+ and Git/gh:
```sh
python runner.py --repo owner/research --checkout /path/to/research --policy policy.json list
python runner.py --repo owner/research --checkout /path/to/research --policy policy.json run --issue 1
python -m unittest discover -s tests -v
```

Issue body must contain a fenced JSON manifest with schema experiment/v1, execution scripted, source (approved clone URL), revision (40 hex commit), command (argv), capabilities (list), timeout (seconds). The command writes report.md and optional flat artifacts to EXPERIMENT_OUTPUT. A valid negative or inconclusive finding exits zero. Nonzero exits are execution failures, not findings.

Leases use Git ref compare-and-swap. Results are committed to unique attempt branches and submitted as PRs; review and merge closes the issue. Claims are advisory among cooperative runners, not authorization. Review duplicate results if leases expire. Do not enable branch rules that prevent lease updates. No daemon or automatic execution is enabled.

## Next steps

Strict schema validation, renewable leases during checkout/publication, explicit failure state and retries, replication slots, container executor with isolation/resource budgets, SSH executor, MCP, local SQLite recovery, bench adapters and local hardware interlocks, contributor UI, artifact storage. GitHub integration and concurrent claims require live validation before production use.

## Additional pinned inputs

Optional manifest field: "inputs": [{"name":"fixtures","repository":"self","revision":"<40 hex SHA>","paths":["fixtures/nvis"]}].
For external inputs use exact HTTPS GitHub clone URLs. Each repository (including the literal self) must appear in local policy allowed_inputs. Explicit repository-relative paths are mandatory. Files are exported directly from Git blobs without checkout filters, symlinks or submodules. EXPERIMENT_INPUTS points to the staging directory, with one child per input name. max_input_bytes limits selected materialized bytes, not network fetch or Git object storage. Inputs have read-only file permissions, which are NOT a security boundary for native processes running as the same user. Container isolation remains required for untrusted workloads. The primary executable source still follows its separate allowed_sources and allow_native policy.

## Container execution

Set execution to container and image to a locally approved immutable image digest (or full local image ID). Set allow_container and allowed_images in local policy. Default runtime is Podman; Docker is also supported but its daemon is privileged on typical installs. The runner disables network, capabilities, privilege escalation, writable root filesystem and image pulling, and mounts source and inputs read-only. No physical devices are passed. Output disk usage is not hard-quota limited yet. Container isolation is defense in depth, not a guarantee against hostile code. Do not grant Docker socket access to jobs.

## Optional AI assistance

inference.py provides a locally configured command adapter, with example presets for Antigravity, Codex, Muse and Claude. The operator must configure an argv explicitly (see PRESETS), opt into evidence transfer, enable the backend and authorize roles. Prompt is passed on stdin or via a literal {prompt} argv placeholder. No shell evaluation, no issue-supplied backend commands. AI is off by default. Report assistance creates a separate ai-draft.md, never modifies the original report or determines success. The generic advise interface also supports advisory management roles but no automated management decisions are wired yet. CLI agents may have their own tools, credentials, external services, or local config: run approved providers in a separately restricted account/environment and verify their permissions before enabling. No live model calls tested.
