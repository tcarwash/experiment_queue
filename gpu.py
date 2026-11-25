"""Explicit, locally approved GPU mappings for isolated container workloads."""
import os
import re

_RENDER = re.compile(r'/dev/dri/renderD[0-9]{1,4}\Z')
_VERSION = re.compile(r'[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}\Z')


def approved(manifest, policy):
    mode = manifest.get('gpu')
    caps = manifest.get('capabilities', [])
    if mode is None:
        return not any(isinstance(c, str) and c.startswith('gpu.') for c in caps)
    if mode not in ('cuda', 'rocm') or manifest.get('execution') != 'container':
        return False
    if not isinstance(caps, list) or f'gpu.{mode}' not in caps:
        return False
    gpu = policy.get('gpu', {})
    if not isinstance(gpu, dict) or gpu.get('enabled') is not True or gpu.get('backend') != mode:
        return False
    if policy.get('container_runtime', 'podman') != 'docker':
        # GPU flag parity with Podman has not been validated.
        return False
    if mode == 'cuda':
        devices = gpu.get('device_ids')
        return (isinstance(devices, list) and 0 < len(devices) <= 16
                and len(set(map(str, devices))) == len(devices)
                and all(isinstance(v, str) and re.fullmatch(r'(0|[1-9][0-9]{0,2})', v) for v in devices))
    devices = gpu.get('render_devices')
    groups = gpu.get('group_ids')
    override = gpu.get('hsa_override_gfx_version')
    return (
        isinstance(devices, list) and 0 < len(devices) <= 8
        and all(isinstance(p, str) and _RENDER.fullmatch(p) for p in devices)
        and len(set(devices)) == len(devices)
        and isinstance(groups, list) and 0 < len(groups) <= 8
        and all(type(g) is int and 1 <= g <= 65535 for g in groups)
        and len(set(groups)) == len(groups)
        and (override is None or (isinstance(override, str) and _VERSION.fullmatch(override)))
    )


def docker_args(manifest, policy):
    mode = manifest.get('gpu')
    if mode is None:
        return []
    if not approved(manifest, policy):
        raise ValueError('GPU allocation is not locally approved')
    cfg = policy['gpu']
    if mode == 'cuda':
        return ['--gpus', 'device=' + ','.join(cfg['device_ids'])]
    args = ['--device', '/dev/kfd']
    for path in cfg['render_devices']:
        args.extend(['--device', path])
    for gid in cfg['group_ids']:
        args.extend(['--group-add', str(gid)])
    if cfg.get('hsa_override_gfx_version'):
        args.extend(['--env', 'HSA_OVERRIDE_GFX_VERSION=' + cfg['hsa_override_gfx_version']])
    return args
