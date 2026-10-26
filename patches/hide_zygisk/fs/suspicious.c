#include <linux/string.h>
#include <linux/types.h>
#include <linux/cred.h>
#include <linux/fs.h>
#include <linux/path.h>
#include <linux/slab.h>
#include <linux/seq_file.h>
#include <linux/printk.h>
#include <linux/mount.h>
#include <linux/namei.h>

#include "mount.h"
#include <linux/uidgid.h>

#define uid_matches() (current_uid().val >= 2000)

static const char* const suspicious_paths[] = {
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
	"/data/local/proot",
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
};

static const char* const suspicious_mount_types[] = {
	"overlay",
	"tmpfs",
	"cgroup",
	"cgroup2",
	"proc",
	"sysfs",
	"deb",
};


static const char* const suspicious_mount_paths[] = {
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
};

static const char* const suspicious_mount_devices[] = {
	"KSU",
	"ksu",
	"su",
	"magisk",
	"zygisk",
	"pad",
	"hide",
	"lkm"
};

int is_suspicious_path(const struct path* const file)
{
	size_t index = 0, size = 4096;
	int res = -1, status = 0;
	char *path = NULL, *ptr = NULL, *end = NULL;

	if (!uid_matches() || file == NULL) {
		status = 0;
		goto out;
	}

	path = kmalloc(size, GFP_KERNEL);
	if (path == NULL) {
		status = -1;
		goto out;
	}

	ptr = d_path(file, path, size);
	if (IS_ERR(ptr)) {
		status = -1;
		goto out;
	}

	end = mangle_path(path, ptr, " \t\n\\");
	if (!end) {
		status = -1;
		goto out;
	}

	res = end - path;
	path[(size_t) res] = '\0';

	for (index = 0; index < ARRAY_SIZE(suspicious_paths); index++) {
		const char* const name = suspicious_paths[index];
		if (memcmp(name, path, strlen(name)) == 0) {
			status = 1;
			goto out;
		}
	}

out:
	kfree(path);
	return status;
}

int suspicious_path(const struct filename* const name)
{
	int status = 0, ret = 0;
	struct path path;

	if (IS_ERR(name)) {
		return -1;
	}

	if (!uid_matches() || name == NULL) {
		return 0;
	}

	ret = kern_path(name->name, LOOKUP_FOLLOW, &path);
	if (ret) {
		return 0;
	}

	status = is_suspicious_path(&path);
	path_put(&path);
	return status;
}

int is_suspicious_mount(struct vfsmount* const mnt, const struct path* const root)
{
	size_t index = 0, size = 4096;
	int res = -1, status = 0;
	char* path = NULL, *ptr = NULL, *end = NULL;
	struct path mnt_path = {
		.dentry = mnt->mnt_root,
		.mnt = mnt
	};
	struct mount* real = real_mount(mnt);

	if (!uid_matches()) {
		status = 0;
		goto out;
	}

	for (index = 0; index < ARRAY_SIZE(suspicious_mount_types); index++) {
		const char* const name = suspicious_mount_types[index];
		if (mnt->mnt_root && mnt->mnt_root->d_sb && mnt->mnt_root->d_sb->s_type && mnt->mnt_root->d_sb->s_type->name) {
			if (strcmp(mnt->mnt_root->d_sb->s_type->name, name) == 0) {
				status = 1;
				goto out;
			}
		}
	}

	path = kmalloc(size, GFP_KERNEL);
	if (path == NULL) {
		status = -1;
		goto out;
	}

	ptr = __d_path(&mnt_path, root, path, size);
	if (IS_ERR(ptr)) {
		status = -1;
		goto out;
	}

	end = mangle_path(path, ptr, " \t\n\\");
	if (!end) {
		status = -1;
		goto out;
	}

	res = end - path;
	path[(size_t) res] = '\0';

	for (index = 0; index < ARRAY_SIZE(suspicious_mount_paths); index++) {
		const char* const name = suspicious_mount_paths[index];
		if (memcmp(path, name, strlen(name)) == 0) {
			status = 1;
			goto out;
		}
	}

	for (index = 0; index < ARRAY_SIZE(suspicious_mount_devices); index++) {
		const char* const name = suspicious_mount_devices[index];
		if (real->mnt_devname != NULL && strcmp(real->mnt_devname, name) == 0) {
			status = 1;
			goto out;
		}
	}



out:
	kfree(path);
	return status;
}
bool suspicious_pid_alive(int pid)
{
	char buf[64];
	struct file *fp;

	/* Only probes from elevated UID (ksu/root context) can call this. */
	if (from_kuid(&init_user_ns, current_euid()) < 2000)
		return false;

	snprintf(buf, sizeof(buf), "/proc/%d", pid);
	fp = filp_open(buf, O_RDONLY, 0);
	if (IS_ERR(fp))
		return false;
	filp_close(fp, NULL);

	/* Existence of /proc/<pid> means the process exists. */
	return true;
}

bool suspicious_modules_list(void)
{
	struct file *fp;

	if (from_kuid(&init_user_ns, current_euid()) < 2000)
		return false;

	fp = filp_open("/proc/modules", O_RDONLY, 0);
	if (IS_ERR(fp))
		return false;

	/* Existence of /proc/modules file is suspicious. */
	filp_close(fp, NULL);
	return true;
}
