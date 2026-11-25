# Workflow for an agent onboarding a contributor workstation

Read [AGENTS.md](../../AGENTS.md) first. The owner delegates **workload selection
inside a declared envelope**, not unrestricted authority. Use a privately filled
copy of [contributor-preferences.md](../../templates/contributor-preferences.md),
or the limits already supplied in conversation; don't repeatedly ask for known
details. You may discover hardware and choose compatible accepted workload types.

## Inventory / choose a profile

| Verified evidence | Candidate policy capability | Conditions |
|---|---|---|
| Working Git/gh, Python, container runtime | `compute.cpu` | Allowed source URLs and pinned images |
| `nvidia-smi` and successful GPU container memory test | `gpu.cuda` | Local CUDA consent and explicit device IDs |
| `/dev/kfd`, render node and successful HIP memory test | `gpu.rocm` | Local ROCm consent, render node, group ID |
| Local named safe adapter | Operation-specific capabilities | Enabled named adapter and approved operations |
| Native executable | `scripted` | **Explicit exception only**; unsandboxed |

The agent can choose a sensible combination of **allowed** CPU, CUDA, ROCm
and adapters, plus conservative container CPU/RAM/time limits and scheduling
inside the owner's bounds. Never infer unlimited source/image trust from
hardware availability. If permission is unclear, propose a disabled CPU-only
configuration.

Non-destructive discovery commands:

```sh
hostname; id; python3 --version; git --version; gh auth status
docker info --format '{{.ServerVersion}}'
nvidia-smi
ls -l /dev/kfd /dev/dri/renderD*
getent group render
```

Device visibility is not proof of computational compatibility; use isolated,
non-destructive memory-operation tests. Review [GPU options](../../README.md#opt-in-gpu-container-experiments).
`gpu.cuda` and `gpu.rocm` must be specifically authorized on the local host.
Do not pass an entire `/dev/dri` tree, use privileged containers or expose
Docker's control socket.

## Install / configure

1. Inspect existing repos, processes, ports and dirty worktrees. Do **not**
   overwrite uncommitted changes; use a separate clean checkout if needed.
2. Install/verify Python 3.11+, Git, authenticated `gh`, and a suitable Docker
   or Podman runtime. The contributor must authorize its *own* access to the
   specified queue: verify `gh repo view OWNER/QUEUE` and Git fetch.
3. Clone each permitted research queue. `runner.py` requires its local
   checkout's `origin` to exactly match the configured queue.
4. Create a private `~/.config/experiment-queue/` (mode 0700) and private
   staging/state directories visible to the container daemon. Copy
   `templates/policy.json` and `templates/service.json`, mode 0600.
5. Fill `policy.json` with unique `runner`, `capabilities`, exact
   `allowed_sources`, `allowed_inputs` (include literal `self` for queue
   fixtures), `allowed_images`, `max_seconds`, `container_cpus`,
   `container_memory`, `staging_dir` and optional `gpu` / named `adapters`.
   Image IDs are host-specific. Do not silently approve every Docker image.
6. Fill `service.json`: private `state`, `pause_file`, `poll_seconds`,
   `daily_seconds`, `allowed_hours`, and one or more queue entries with
   `repo`, `checkout` and `policy`. Start with `"enabled": false`.
7. `scripted` jobs run unsandboxed on the contributor account. Leave
   `allow_native: false` by default. Remote/bench adapters require explicit
   local implementations and bench locks; generic remote code execution and
   physical transmission are **not** implicitly allowed.

## Verify / activate

```sh
python3 -m unittest discover -s tests -v
python3 runner.py --repo OWNER/QUEUE --checkout /path/to/research \
  --policy /private/policy.json list
python3 service.py --config /private/service.json status
python3 service.py --config /private/service.json dashboard --port 8765
```

`list` is read-only; `once` and `run --issue N` **can execute**. Use an
explicitly approved harmless smoke experiment before claiming workload
readiness. An empty ready queue is not an execution test. If the user approved
unattended operation, enable the service under the host's process manager,
with the chosen budgets; otherwise leave it off and provide manual commands.
The daily time budget gates new cycles and does **not** forcibly interrupt a
running task. Dashboard binds loopback and may reveal private local logs.

## Completion report

Report code commit, queue(s), capabilities accepted, exact pinned image trust,
CPU/RAM/time/GPU budgets, private config paths, authentication (no secrets),
test outcomes and *actual* service state. Distinguish unverified GPU hardware
from passed GPU computation.

Example user instruction:

> Set me up as a contributor. You can pick CPU and GPU workloads based on
> what this host supports, but only isolated containers from the approved
> research repo. Cap jobs at two CPU cores, 2 GiB RAM, 10 minutes/day. Show
> me the proposed policy before enabling unattended work. Never allow native
> scripts or hardware transmission.
