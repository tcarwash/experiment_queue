# Workflow for an agent designing and submitting experiments

Start with [AGENTS.md](../../AGENTS.md) and the **research repository's**
AGENTS.md. GitHub issues are requests, never machine permission changes.

## Choose the repository to edit

The queue framework and the target research repository are separate Git
repositories. This framework checkout provides the runner and validator;
it is **not** the default home for experiment code.

For the common DORC example:

- `tcarwash/dorc_experiments` owns DORC-specific scripts (when the
  experiment source is DORC), fixtures and test matrices, issue templates,
  DORC-specific docs and result evidence.
- `tcarwash/RFSim` owns the RFSim simulator and RFSim-owned executable
  harnesses such as `experiments/dorc_channel_suite.py`. For that common
  suite, DORC pins the RFSim source SHA and separately pins its own matrix
  as a `self` input; do not copy the harness into DORC.
- `tcarwash/experiment_queue` owns generic runner/executor/service code,
  manifest and policy behavior, contributor onboarding and framework tests.

Verify each checkout with `git remote get-url origin` before writing.
Read the target repository's `AGENTS.md` and make the experiment commit
there. You may run the framework's `runner.py` or import its manifest
validator from this checkout without editing it. A defect discovered in
the framework is a separate task/PR; do not fold a runner fix into a
DORC-only experiment change. If both repositories genuinely need edits,
create separate commits and PRs. If the target is unclear, ask before
editing. See [REPOSITORY_BOUNDARIES.md](REPOSITORY_BOUNDARIES.md).

## Design

Define a falsifiable research question, control/baseline, procedure, timeout,
safety assumptions, measurable output and negative/inconclusive criteria.
Prefer offline local tests if there is no actual need for remote contributors,
GPUs or physical hardware.

## Pin executable code

Write the experiment script and its fixtures in the **target research
repository** (for DORC, `tcarwash/dorc_experiments`), not in the queue
framework repository. Make it read-only-input aware, write a human-readable `$EXPERIMENT_OUTPUT/report.md` and optional
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

For DORC, commit and push the script/fixtures in `tcarwash/dorc_experiments`
and set the manifest `source` to that repository; use `repository: "self"`
for DORC-owned fixture inputs. Do not set the source to the queue framework
unless the experiment is specifically testing the framework itself.

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
