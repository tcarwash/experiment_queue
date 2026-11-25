# Repository boundaries for multi-repository agent work

This document is the routing contract for workspaces containing both the
queue framework and one or more research repositories. The repositories are
separate projects, not a monorepo. Their `AGENTS.md` files apply to their
own checkout only.

## Canonical ownership

| Repository | Owns | Does not own |
|---|---|---|
| `tcarwash/experiment_queue` (this repository) | Generic runner, executors, scheduler/service, queue protocol, manifest and policy semantics, reusable onboarding/authoring docs, framework tests | DORC-specific experiment scripts, DORC fixtures/matrices, DORC issue templates, and DORC result artifacts |
| `tcarwash/dorc_experiments` | DORC-owned experiment scripts (such as the example smoke test), fixture data and matrices, DORC procedures/templates/issues, accepted reports and provenance | Generic runner, executor, scheduler, or contributor-policy implementation |
| `tcarwash/RFSim` | RFSim simulator implementation, its tests, and RFSim-owned executable experiment harnesses such as `experiments/dorc_channel_suite.py` | DORC queue issues, DORC-owned matrix inputs, and DORC result records |

For the RFSim common-suite example, the executable and simulator code live
in `RFSim`; the shared profile/SNR/seed matrix, issue templates, queue
requests and accepted result records live in `dorc_experiments`. The queue
runner and its execution policy live here. Keep these three responsibilities
separate even when a single experiment uses all three repositories.

## Route the task before editing

- "Implement/run/add an experiment", "change the DORC example", "update its
  fixtures/matrix/template", or "review its result" means edit
  **`tcarwash/dorc_experiments`**, not this framework repository.
- "Change the queue runner/service/executor/manifest contract", "fix generic
  issue claiming/publication", or "change contributor onboarding" means edit
  **`tcarwash/experiment_queue`**.
- "Change RFSim propagation/channel implementation" means edit
  **`tcarwash/RFSim`**.
- If a DORC experiment exposes a runner defect, record the defect and request
  a separate framework task. Do not patch the framework merely because its
  checkout is available beside the experiment.
- If a task genuinely needs multiple repositories, make separate changes,
  commits and pull requests in each repository, and state the dependency
  between them. Never mix files from two repositories in one commit.
- If the requested target is ambiguous (especially "main repo"), ask which
  canonical repository the user means before editing.

## Two-checkout preflight

Before the first write, identify each checkout by its Git remote and root;
never infer identity from its directory name or current working directory:

```sh
git -C /path/to/experiment-queue remote get-url origin
git -C /path/to/dorc_experiments remote get-url origin
git -C /path/to/RFSim remote get-url origin
git -C /path/to/target rev-parse --show-toplevel
git -C /path/to/target status --short
```

Confirm the remote matches the intended task. Read the target repository's
own `AGENTS.md` and local instructions before editing. Instructions from
two checkouts do not combine into permission to write to both: the task's
target repository is the write scope.

When authoring a DORC experiment, commit its executable source and fixtures
in `tcarwash/dorc_experiments`, pin that pushed SHA in the manifest, and
use `repository: "self"` for DORC-owned fixture inputs. The queue framework
checkout may be used read-only to run `runner.py`, validate a manifest or
inspect runner behavior. For example, `runner.py --checkout` names the
DORC checkout; it does not make the framework checkout the experiment's
source or edit target.

Keep each repository's `git status`, staging, commits and PRs separate.
Do not run `git add .` from a workspace parent that contains multiple
repositories. If a separate framework fix is explicitly requested, make it
in the framework checkout and link its PR from the DORC work.
