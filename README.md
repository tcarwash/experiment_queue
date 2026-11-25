# Experiment Runner

A contributor-controlled, GitHub-backed distributed research queue.
Execution remains opt-in and potentially risky: do not execute untrusted
workloads outside an appropriately isolated account or host.

## Agent-oriented workflows

Point an agent at [AGENTS.md](AGENTS.md). The
[contributor setup guide](docs/agents/CONTRIBUTOR_SETUP.md) allows an agent
to inspect a workstation and **choose acceptable CPU/GPU/adapter workloads**
inside an owner-approved resource and trust envelope. The
[experiment authoring guide](docs/agents/EXPERIMENT_AUTHORING.md) covers
pinned source, manifests and evidence. An operator can give an agent a filled
[private preferences template](templates/contributor-preferences.md) rather
than selecting each workload individually. Copilot roles are under
`.github/agents/`; `CLAUDE.md` and `GEMINI.md` share the instructions.

## Quick start

Create a private research repository with a default branch and label `experiment-ready`. Clone it locally, authenticate Git and gh, and copy templates/policy.json to policy.json. Explicitly approve native execution and trusted source URLs only on a dedicated account or machine. Native execution is NOT sandboxed: the child can access the user's files, network and credentials despite the reduced environment.

Use Python 3.11+ and Git/gh:
```sh
python runner.py --repo owner/research --checkout /path/to/research --policy policy.json list
python runner.py --repo owner/research --checkout /path/to/research --policy policy.json run --issue 1
python -m unittest discover -s tests -v
```

Issue body must contain a fenced JSON manifest with schema `experiment/v1`,
execution `container` (recommended), source (approved clone URL), revision
(full 40-hex pushed commit), image (approved immutable ID/digest), command
(argv), capabilities (list), and timeout (seconds). The command writes report.md and optional flat artifacts to EXPERIMENT_OUTPUT. A valid negative or inconclusive finding exits zero. Nonzero exits are execution failures, not findings.

Leases use Git ref compare-and-swap. Results are committed to unique attempt branches and submitted as PRs; review and merge closes the issue. Claims are advisory among cooperative runners, not authorization. Review duplicate results if leases expire. Do not enable branch rules that prevent lease updates. A persistent scheduler is available but is disabled by default.

## Operational limitations

This project has an opt-in persistent scheduler, result/recovery support, and
local CPU/GPU execution, but it is **not** an unrestricted multi-tenant compute
service. A typical Docker daemon is privileged; GPU device access broadens
kernel exposure. Podman/GPU portability, hard output storage limits, process
recovery after crashes and hard per-day execution cutoffs are not fully
implemented. The MCP interface is read-only. Physical bench and remote
execution require contributor-supplied adapters and local safety controls.

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

## Remote compute and physical bench adapters

The remote and bench execution kinds dispatch to a locally installed adapter. The issue names an adapter and an allowed operation, and passes JSON parameters. Local policy defines adapters by name with enabled, kind, argv (absolute executable path), allowed_operations, and optionally lock_file (mandatory for bench). The adapter receives one JSON argument with paths to staged source, inputs, output, operation, parameters, timeout and attempt ID. No issue-supplied shell command is executed by this interface. Bench adapters share an exclusive local flock. The adapter itself must validate parameters, enforce device safety, handle remote cancellation, and write report.md. No production SSH or instrument-specific adapter is bundled yet. Use a dedicated low-privilege adapter account and do not enable arbitrary operations.

## Experiment campaigns (experimental)

A manifest may include `"depends_on":[12,15]` and `"replication":{"desired_runs":3,"distinct_runners":true}`. Dependencies must be closed issues with enough accepted records on the queue's default branch. Results from a different manifest revision do not count. Replication is serialized through the issue lease. A result is *pending* while its pull request remains unmerged; accepted results are those already committed to the queue's default branch. The runner searches for pushed result branches and re-creates a missing PR after an interrupted publication. These workflows have local Git integration tests but not a complete live multi-replication campaign. For multi-run experiments, a later runner invocation reconciles accepted counts and closes completed issues. Manual PR rejections, changed manifests, and long-running recovery still need an explicit periodic reconciler. Do not treat an issue's closed state alone as experimental evidence.

## Opt-in GPU container experiments

Only Docker GPU containers are currently supported. A manifest must explicitly request
`"gpu":"cuda"` with `"gpu.cuda"` in capabilities, or
`"gpu":"rocm"` with `"gpu.rocm"` in capabilities. A CPU-only manifest
never receives GPU devices, even on a GPU-equipped runner.

Each contributor authorizes GPU access **locally**, as well as separately allowlisting
the exact immutable container image digest. The GPU configuration cannot be supplied
or overridden by a GitHub issue.

For a CUDA host with a compatible NVIDIA container toolkit:

```json
{
  "capabilities": ["compute.cpu", "gpu.cuda"],
  "gpu": {"enabled": true, "backend": "cuda", "device_ids": ["0"]}
}
```

For an AMD ROCm host:

```json
{
  "capabilities": ["compute.cpu", "gpu.rocm"],
  "gpu": {
    "enabled": true,
    "backend": "rocm",
    "render_devices": ["/dev/dri/renderD128"],
    "group_ids": [110]
  }
}
```

The above are fields inside the local policy (not complete policies). The AMD group ID
must match the host's `render` access group, and the render node must be the
intended GPU. The AMD mapping grants access to `/dev/kfd` plus only approved
render nodes. A strictly local optional `hsa_override_gfx_version` value (e.g.
`"10.3.0"`) passes the corresponding ROCm environment variable, but **cannot
guarantee that unsupported AMD cards actually execute HIP kernels**.

Add to a pinned-source **container** experiment manifest:

```json
{
  "gpu": "cuda",
  "capabilities": ["compute.cpu", "gpu.cuda"]
}
```

Use `"rocm"` and `"gpu.rocm"` for an AMD experiment. A CUDA request never
runs on a ROCm-only host and vice versa. The GPU field cannot be used with native,
remote, or bench execution. Without GPU consent the runner rejects the manifest.
No issue-supplied Docker GPU flags, render nodes, group IDs, or override values
are honored.

GPU devices expose a greater kernel and driver attack surface than CPU-only
containers. GPU memory capacity is **not** governed by the Docker `--memory`
limit. Contributors must account for GPU VRAM separately and limit concurrent
GPU experiments locally. NVIDIA `device_ids` are Docker-visible device indexes,
not a promise of workload compatibility. Pascal (compute 6.1) requires software
that supports that target. The GPU features are an opt-in privilege; users should
not enable them for untrusted experiments without appropriate host isolation.

