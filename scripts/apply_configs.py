#!/usr/bin/env python3
# apply_configs.py - Direct .config modifier for Carbon Kernel build.
# Replaces `scripts/config` to avoid kallsyms_decode_symbol link error.
# Usage:
#   python3 apply_configs.py -e KSU KSU_SUSFS ...
#   python3 apply_configs.py -d KSU KSU_SUSFS ...
#   python3 apply_configs.py --set-str LOCALVERSION "-Carbon-cupid"

import sys
from pathlib import Path

CONFIG = Path('out/.config')

def parse_args(argv):
    ops = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '-e':
            i += 1
            if i < len(argv):
                ops.append(('enable', argv[i]))
        elif a == '-d':
            i += 1
            if i < len(argv):
                ops.append(('disable', argv[i]))
        elif a == '--set-str':
            i += 1
            if i + 1 < len(argv):
                ops.append(('setstr', argv[i], argv[i+1]))
                i += 1
        elif '=' in a and a.startswith('-e'):
            # -e KEY=value
            op, val = a.split('=', 1)
            ops.append(('enable', op, val))
        i += 1
    return ops

def patch_config(ops):
    if not CONFIG.exists():
        print(f"ERROR: {CONFIG} not found. Run make first.")
        sys.exit(1)

    lines = CONFIG.read_text(encoding='utf-8').splitlines(keepends=True)
    modified = set()

    for op in ops:
        if op[0] == 'enable':
            key = op[1]
            val = 'y'
            if len(op) > 2:
                val = op[2]
            # Enable: remove '# CONFIG_KEY is not set' and set to =y or =m
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped == f'# {key} is not set':
                    lines[idx] = f'{key}={val}\n'
                    modified.add(key)
                    break
                if stripped.startswith(f'CONFIG_{key}='):
                    if stripped.startswith('#'):
                        lines[idx] = stripped[1:].lstrip()
                    else:
                        parts = stripped.split('=', 1)
                        lines[idx] = f'CONFIG_{parts[0]}={val}\n'
                    modified.add(key)
                    break

        elif op[0] == 'disable':
            key = op[1]
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped == f'# {key} is not set':
                    break
                if stripped.startswith(f'CONFIG_{key}='):
                    if stripped.startswith('#'):
                        lines[idx] = stripped[1:].lstrip()
                    # Convert to unset
                    lines[idx] = f'# {key} is not set\n'
                    modified.add(key)
                    break

        elif op[0] == 'setstr':
            key, val = op[1], op[2]
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(f'CONFIG_{key}=') and not stripped.startswith('#'):
                    # Replace existing value
                    lines[idx] = f'CONFIG_{key}="{val}"\n'
                    modified.add(key)
                    break
                if stripped == f'# {key} is not set':
                    pass
            else:
                # Add at end
                lines.append(f'CONFIG_{key}="{val}"\n')

    CONFIG.write_text(''.join(lines), encoding='utf-8')
    if modified:
        print(f"Config updated: {', '.join(modified)}")
    else:
        print("No config changes applied.")

if __name__ == '__main__':
    patch_config(parse_args(sys.argv[1:]))
