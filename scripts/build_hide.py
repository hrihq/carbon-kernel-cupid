#!/usr/bin/env python3
# Patch hide level for Carbon Kernel
from pathlib import Path

def patch_suspicious_c():
    p = Path('patches/hide_zygisk/fs/suspicious.c')
    s = p.read_text()

    # Expand suspicious_paths
    old = """static const char* const suspicious_paths[] = {
	"/storage/emulated/0/TWRP",
	"/system/lib/libzygisk.so",
	"/system/lib64/libzygisk.so",
	"/dev/zygisk",
	"/system/addon.d",
	"/vendor/bin/install-recovery.sh",
	"/system/bin/install-recovery.sh",
	"/debug_ramdisk",
	"/data/adb"
};"""
    new = """static const char* const suspicious_paths[] = {
	"/storage/emulated/0/TWRP",
	"/system/lib/libzygisk.so",
	"/system/lib64/libzygisk.so",
	"/dev/zygisk",
	"/system/addon.d",
	"/vendor/bin/install-recovery.sh",
	"/system/bin/install-recovery.sh",
	"/debug_ramdisk",
	"/data/adb",
	"/data/adb/modules",
	"/data/adb/modules.load",
	"/data/adb/dalvikvm.opt",
	"/data/adb/fs_config",
	"/data/adb/rdir",
	"/data/local",
	"/data/local/tmp",
	"/data/local/xposed",
	"/data/local/bin",
	"/data/misc",
	"/data/system",
	"/data/system/packages.xml",
	"/data/system/packages.list",
	"/data/system/debuggable",
	"/data/resource-overlay",
	"/data/property",
	"/data/dalvik-cache",
	"/data/app",
	"/data/app/*",
	"/data/iza",
	"/data/media",
	"/data/test-keys",
	"/cache",
	"/oem",
	"/vendor/bin",
	"/vendor/etc",
	"/vendor/firmware",
	"/firmware",
	"/modprobe.d",
	"/etc/init.d",
	"/etc/init",
	"/init.rc",
	"/default.prop",
	"/build.prop",
	"/ro.build.fingerprint",
	"/ro.product.model",
	"/ro.product.device",
	"/proc",
	"/proc/kallsyms",
	"/proc/modules",
	"/proc/cmdline",
	"/proc/bootconfig",
	"/proc/self",
	"/proc/<pid>",
	"/sys",
	"/sys/kernel/debug",
	"/sys/kernel/profiling_data",
	"/sys/module",
	"/sys/bus",
	"/sys/firmware",
	"/sys/devices/system",
	"/dev",
	"/dev/kmem",
	"/dev/mem",
	"/dev/gpmem",
	"/dev/pmem",
	"/dev/ptmx",
	"/dev/kmsg",
	"/dev/zygote",
	"/dev/__properties__",
	"/root",
	"/sbin",
	"/bin",
	"/usr/sbin",
	"/usr/bin",
	"/lib",
	"/lib64",
	"/system",
	"/system/bin",
	"/system/xbin",
	"/system/lib",
	"/system/lib64",
	"/system/framework",
	"/system/priv-app",
	"/system/app",
	"/product",
	"/odm",
	"/vendor",
	"/asus",
	"/panasonic",
	"/samsung",
	"/motorola",
	"/oneplus",
	"/google",
	"/gms",
	"/gms/.core",
	"/apex",
	"/system/apex",
	"/system/ext",
	"/system/priv-app",
	"/system/recovery",
	"/system/lib/modules",
	"/system/lib64/modules"
};"""
    if old in s:
        s = s.replace(old, new, 1)
        print('  [ok] suspicious_paths expanded')
    else:
        print('  [warn] suspicious_paths pattern not found')

    # Expand suspicious_mount_types
    old = """static const char* const suspicious_mount_types[] = {
	"overlay"
};"""
    new = """static const char* const suspicious_mount_types[] = {
	"overlay",
	"tmpfs",
	"cgroup",
	"cgroup2",
	"proc",
	"sysfs",
	"dev"
};"""
    if old in s:
        s = s.replace(old, new, 1)
        print('  [ok] suspicious_mount_types expanded')
    else:
        print('  [warn] suspicious_mount_types pattern not found')

    # Expand suspicious_mount_paths
    old = """static const char* const suspicious_mount_paths[] = {
	"/data/adb",
	"/data/app",
	"/apex/com.android.art/bin/dex2oat",
	"/system/apex/com.android.art/bin/dex2oat",
	"/system/etc/preloaded-classes",
	"/dev/zygisk",
	"/debug_ramdisk"
};"""
    new = """static const char* const suspicious_mount_paths[] = {
	"/data/adb",
	"/data/app",
	"/data/app/*",
	"/apex/com.android.art/bin/dex2oat",
	"/system/apex/com.android.art/bin/dex2oat",
	"/system/etc/preloaded-classes",
	"/dev/zygisk",
	"/debug_ramdisk",
	"/proc/kallsyms",
	"/proc/modules",
	"/proc/cmdline",
	"/proc/<pid>",
	"/sys/kernel/debug",
	"/sys/kernel/profiling_data",
	"/sys/module",
	"/sys/bus",
	"/sys/firmware",
	"/sys/devices/system",
	"/dev/kmem",
	"/dev/mem",
	"/dev/ptmx",
	"/dev/__properties__",
	"/proc/1/ns/mnt",
	"/proc/self/ns/mnt"
};"""
    if old in s:
        s = s.replace(old, new, 1)
        print('  [ok] suspicious_mount_paths expanded')
    else:
        print('  [warn] suspicious_mount_paths pattern not found')

    # Expand suspicious_mount_devices
    old = """static const char* const suspicious_mount_devices[] = {
	"KSU"
};"""
    new = """static const char* const suspicious_mount_devices[] = {
	"KSU",
	"ksu",
	"su",
	"magisk",
	"zygisk",
	"pad",
	"hide",
	"lkm"
};"""
    if old in s:
        s = s.replace(old, new, 1)
        print('  [ok] suspicious_mount_devices expanded')
    else:
        print('  [warn] suspicious_mount_devices pattern not found')

    p.write_text(s)
    print('  done suspicious.c')

def patch_suspicious_h():
    p = Path('patches/hide_zygisk/include/linux/suspicious.h')
    s = p.read_text()
    old = """int is_suspicious_path(const struct path* const file);
int is_suspicious_mount(struct vfsmount* const mnt, const struct path* const root);
int suspicious_path(const struct filename* const name);"""
    new = """int is_suspicious_path(const struct path* const file);
int is_suspicious_mount(struct vfsmount* const mnt, const struct path* const root);
int suspicious_path(const struct filename* const name);
bool suspicious_pid_alive(int pid);
bool suspicious_modules_list(void);"""
    if old in s:
        s = s.replace(old, new, 1)
        print('  [ok] suspicious.h updated')
    else:
        print('  [warn] suspicious.h pattern not found')
    p.write_text(s)

def patch_apply_tweaks():
    p = Path('scripts/apply_tweaks.py')
    s = p.read_text()
    if '8e. Procfs/sysfs hiding' not in s:
        additional = '''
# 8e. Procfs/sysfs hiding: hide /proc/kallsyms, /proc/modules, /proc/cmdline, etc.
for target_path, target_regex, replace in [
    ("fs/proc_kallsyms.c", "show_symbol", "return 0; // Hide kernel symbols"),
    ("fs/proc_modules.c", "show_module", "return 0; // Hide modules"),
    ("fs/proc_cmdline.c", "show_arg", "return 0; // Hide cmdline"),
    ("fs/proc_self_status.c", "show_status", "return 0; // Hide self status"),
    ("fs/proc_pid_devpts.c", "show_devpts", "return 0; // Hide devpts"),
]:
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            c = f.read()
        if target_regex in c:
            c = c.replace(target_regex, replace, 1)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(c)
            print(f"Patched {target_path} with hiding hook")
    except Exception as e:
        print(f"ERROR patching {target_path}: {e}")

# 8f. Cgroup namespace hiding: hide cgroup mounts
try:
    with open("fs/proc_cgroup.c", "r", encoding="utf-8") as f:
        c = f.read()
    if "cgroup" in c and "mount" in c:
        c = c.replace("cgroup", "// cgroup", 1)
        with open("fs/proc_cgroup.c", "w", encoding="utf-8") as f:
            f.write(c)
        print("Patched fs/proc_cgroup.c")
except Exception as e:
    print(f"ERROR patching fs/proc_cgroup.c: {e}")

# 8g. PID namespace hiding: hide PIDs
try:
    with open("fs/proc_pid_cmdline.c", "r", encoding="utf-8") as f:
        c = f.read()
    if "pid" in c:
        c = c.replace("pid", "// pid", 1)
        with open("fs/proc_pid_cmdline.c", "w", encoding="utf-8") as f:
            f.write(c)
        print("Patched fs/proc_pid_cmdline.c")
except Exception as e:
    print(f"ERROR patching fs/proc_pid_cmdline.c: {e}")

# 8h. Additional hiding in kernel sources
try:
    with open("kernel/trace/trace.h", "r", encoding="utf-8") as f:
        c = f.read()
    if "trace" in c.lower():
        c = c.replace("trace", "// trace", 1)
        with open("kernel/trace/trace.h", "w", encoding="utf-8") as f:
            f.write(c)
        print("Patched kernel/trace/trace.h")
except Exception as e:
    print(f"ERROR patching kernel/trace/trace.h: {e}")
'''
        if additional not in s:
            s = s.rstrip() + '\n' + additional
            print('  [ok] added additional hiding hooks to apply_tweaks.py')
        else:
            print('  [info] apply_tweaks.py already has additional hooks')
    else:
        print('  [info] apply_tweaks.py already has additional hooks')
    p.write_text(s)

if __name__ == '__main__':
    patch_suspicious_c()
    patch_suspicious_h()
    patch_apply_tweaks()
    print('All done')
