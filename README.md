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

### Runner selection and role routing

Use `once` instead of `run --issue N` to claim and execute at most one eligible ready issue; a contention loss skips to the next candidate. The issue state, label and body are rechecked after acquiring a lease. No automatic service is installed. Use `review --issue N` for optional advisory management review without claiming or executing work. AI role_backends maps individual roles to locally approved backend names, falling back to ai.backend. Only report and explicit management review are wired. Set staging_dir to an existing private directory visible to the container daemon if it cannot see /tmp. Live Docker smoke test confirmed read-only mounts and writable output with a shared staging path. Podman remains untested.

## Persistent contributor service

Copy templates/service.json to a private location and configure its queue entries as objects with repo, checkout and policy. Enable explicitly. Run:

```sh
python service.py --config /path/service.json once
python service.py --config /path/service.json serve
python service.py --config /path/service.json dashboard --port 8765
python service.py --config /path/service.json status
```

The scheduler runs sequentially, records SQLite cycle history, supports a pause file and allowed local hours, and checks a rolling daily wall-time budget before starting each queue cycle. The budget is not a hard running-job cutoff. Interrupted cycle records are marked at restart; orphan processes and publication recovery are not yet reconciled. The dashboard is read-only and binds loopback only; logs may contain private data. Do not proxy it publicly. Use a private state directory.

## Search and MCP

`python findings.py /path/checkout "negative finding"` searches locally committed report text. Fetch the research repository first if freshness matters. The stdio MCP server exposes read-only list_experiments and search_findings. Start `python mcp_server.py --config /private/mcp.json` with JSON fields repo, checkout, policy (path). No execution or mutation through MCP yet.
