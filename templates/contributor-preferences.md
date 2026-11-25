# Contributor autonomy envelope (copy **privately**, not tracked)

Give an agent a filled-in copy as `~/.config/experiment-queue/CONTRIBUTOR.md`
and request setup *within these boundaries*. This file is human/agent guidance,
**not** parsed directly by the runner; the agent must create the real policy.json.

## Trust / scope
- Allowed research queues (owner/repo):
- Trusted source Git URLs (specific repositories):
- Trusted pinned container images (or which images the agent may propose for review):
- Workload types permitted in principle: CPU containers / CUDA / ROCm / named remote/bench adapter
- Native unsandboxed scripts: **no** by default (separate explicit exception)
- Agent autonomy: propose only / configure + test / configure + test + run unattended

## Maximum resource budget
- CPU cores/job:
- RAM/job:
- GPU device count and VRAM expectations:
- Wall time/job:
- Cumulative runtime/day:
- Allowed local hours:
- Output/storage limits:
- Concurrent GPU jobs: **no** by default

## What the agent may decide without asking again

Within the above envelope, the agent may choose **fewer** capabilities, safer
resource budgets, the correct GPU device mapping, pre-approved pinned images,
and a polling interval. Expanding source/image trust, enabling native code,
adding physical hardware access, or switching on unattended jobs outside the
autonomy choice above still requires explicit operator consent.

## Host-specific considerations
- Existing services or GPUs to avoid disrupting:
- Private staging directory visible to the container daemon:
- GitHub authentication method (do not paste tokens):
- Other restrictions:
