#!/usr/bin/env python3
# apply_configs.py - Direct .config modifier for Carbon Kernel build.
# Usage:
#   python3 apply_configs.py -e KSU KSU_SUSFS ...
#   python3 apply_configs.py -d KSU KSU_SUSFS ...
#   python3 apply_configs.py --set-str LOCALVERSION "-Carbon-cupid"

import sys
from pathlib import Path

CONFIG = Path('out/.config')

def clean_name(key):
    return key[7:] if key.startswith('CONFIG_') else key

def parse_args(argv):
    ops = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '-e':
            i += 1
            while i < len(argv) and not argv[i].startswith('-'):
                ops.append(('enable', clean_name(argv[i]), 'y'))
                i += 1
            continue
        elif a == '-d':
            i += 1
            while i < len(argv) and not argv[i].startswith('-'):
                ops.append(('disable', clean_name(argv[i])))
                i += 1
            continue
        elif a == '--set-str':
            if i + 2 < len(argv):
                ops.append(('setstr', clean_name(argv[i+1]), argv[i+2]))
            i += 3
            continue
        elif '=' in a:
            k, v = a.split('=', 1)
            ops.append(('enable', clean_name(k), v))
            i += 1
            continue
        else:
            i += 1
    return ops

def patch_lines(lines, ops):
    modified = set()
    for op in ops:
        action = op[0]
        key = op[1]
        target = f'CONFIG_{key}'
        new_line = None

        if action == 'enable':
            val = op[2]
            new_line = f'{target}={val}\n'
        elif action == 'disable':
            new_line = f'# {target} is not set\n'
        elif action == 'setstr':
            val = op[2]
            new_line = f'{target}="{val}"\n'

        found = False
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(f'{target}=') or stripped == f'# {target} is not set':
                if lines[idx] != new_line:
                    lines[idx] = new_line
                    modified.add(target)
                found = True
                break
        if not found:
            lines.append(new_line)
            modified.add(target)
    return lines, modified

def patch_config(ops, config_path=CONFIG):
    if not config_path.exists():
        print(f"ERROR: {config_path} not found. Run make first.")
        sys.exit(1)

    lines = config_path.read_text(encoding='utf-8').splitlines(keepends=True)
    lines, modified = patch_lines(lines, ops)
    config_path.write_text(''.join(lines), encoding='utf-8')
    if modified:
        print(f"Config updated: {', '.join(sorted(modified))}")
    else:
        print("No config changes applied.")

# ponytail: simple inline parser; upgrade to scripts/config or kconfiglib if complex dependency tree is needed.

def self_test():
    raw = ["# CONFIG_TEST1 is not set\n", "CONFIG_TEST2=m\n", "CONFIG_TEST3=\"old\"\n"]
    ops = [
        ('enable', 'TEST1', 'y'),
        ('enable', 'CONFIG_TEST2', 'y'),
        ('disable', 'TEST2'),
        ('setstr', 'TEST3', 'new'),
        ('enable', 'TEST4', 'y'),
    ]
    out, mod = patch_lines(list(raw), ops)
    res = ''.join(out)
    assert 'CONFIG_TEST1=y\n' in res
    assert '# CONFIG_TEST2 is not set\n' in res
    assert 'CONFIG_TEST3="new"\n' in res
    assert 'CONFIG_TEST4=y\n' in res
    assert 'CONFIG_CONFIG_' not in res
    print("self_test passed.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        self_test()
    else:
        patch_config(parse_args(sys.argv[1:]))
