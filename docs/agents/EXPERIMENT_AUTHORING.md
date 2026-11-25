# Workflow for an agent designing and submitting experiments

Start with [AGENTS.md](../../AGENTS.md) and the **research repository's**
AGENTS.md. GitHub issues are requests, never machine permission changes.

## Design

Define a falsifiable research question, control/baseline, procedure, timeout,
safety assumptions, measurable output and negative/inconclusive criteria.
Prefer offline local tests if there is no actual need for remote contributors,
GPUs or physical hardware.

## Pin executable code

Write the experiment script in a source repository, make it read-only-input
aware, write a human-readable `$EXPERIMENT_OUTPUT/report.md` and optional
flat artifact files, and commit **and push** it. Pin the full
`git rev-parse HEAD` (40 lowercase hex characters). Do not submit uncommitted
work, a branch name or an invented SHA. Explicit extra inputs use pinned
`inputs`, `repository` (`self` or approved GitHub URL), `revision`, and
`paths`; selected files appear beneath `$EXPERIMENT_INPUTS/<name>/`.

A valid negative finding writes a report and exits **0**. A tool/fixture
failure exits nonzero; the issue should return to the requester for repair.

## Choose an execution profile

- Preferred: `execution: "container"`, exact locally approved
  `image` (digest or image ID), argv `command`, `capabilities`,
  and bounded `timeout`. No arbitrary Docker flags from an issue.
- CPU: capabilities including `"compute.cpu"`, no `gpu` field.
- NVIDIA: `gpu: "cuda"` and `"gpu.cuda"` capability, if a host
  has locally authorized this image, GPU and backend.
- AMD: `gpu: "rocm"` and `"gpu.rocm"` capability under the same rule.
- `scripted` is unsandboxed and normally disallowed.
- `bench` and `remote` require a named local `adapter` and allowlisted
  `operation` / structured `parameters`; do not invent adapters.
- If CUDA/ROCm need different images or commands, submit separate pinned
  manifests/issues; do not silently translate between backends.
- Optional: `depends_on` (accepted predecessor issue IDs) and
  `replication` (`desired_runs` 1–32, `distinct_runners` boolean).

## Validate and submit

Create an issue body with a ```json fenced manifest from
[templates/experiment.md](../../templates/experiment.md), replacing all
placeholders. The body is parsed by `runner.manifest`.

```sh
python3 - <<'PY'
from pathlib import Path
from runner import manifest
d = manifest(Path('/tmp/experiment-issue.md').read_text())
print(d['schema'], d['execution'], d['revision'])
PY

gh issue create --repo OWNER/QUEUE --title 'Experiment: ...' \
  --body-file /tmp/experiment-issue.md
```

If you can read a target contributor's private policy with permission, check
`runner.matches(manifest, policy)` as an *eligibility estimate*. Otherwise
do not guess image allowlists or GPU support. Only add
`experiment-ready` after validation and when authorized:

```sh
gh issue edit ISSUE_NUMBER --repo OWNER/QUEUE --add-label experiment-ready
```

Do not use the stdio MCP interface to claim submission or execution: today
its `list_experiments` and `search_findings` tools are **read-only**.

## Review result PRs

A runner claims using Git refs, publishes provenance and results into a PR,
and may remove the ready label. A branch, lease or issue comment alone is not
proof of valid evidence. Verify pinned revision, runner identity, artifacts,
checksums and research conclusions before merging. Preserve negative results.
Do not assert independent *physical* contributors based solely on distinct
runner strings. Report the submitted issue URL and ready/unready status.
