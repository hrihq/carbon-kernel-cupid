import sys

def patch(filepath, old, new):
    with open(filepath, 'r', encoding='utf-8') as f:
        c = f.read()
    if old not in c:
        print(f"ERROR: Target string not found in {filepath}:\n{repr(old)}")
        sys.exit(1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(c.replace(old, new, 1))
    print(f"Patched {filepath} successfully!")

# 1. WALT Scheduler: Scroll Cooling (keep light tasks on Little A510 cores, sleep Cortex-X2)
patch("kernel/sched/walt/sysctl.c",
      "unsigned int sysctl_sched_min_task_util_for_boost = 51;",
      "unsigned int sysctl_sched_min_task_util_for_boost = 100;")

patch("kernel/sched/walt/sysctl.c",
      "unsigned int sysctl_sched_min_task_util_for_colocation = 35;",
      "unsigned int sysctl_sched_min_task_util_for_colocation = 70;")

# 2. WALT Scheduler: Fast Core Release & Downmigrate for Snapdragon 8 Gen 1 (tame CPU thermals)
patch("kernel/sched/walt/sysctl.c",
      "\tsysctl_sched_coloc_busy_hyst_max_ms = 5000;",
      "\tsysctl_sched_coloc_busy_hyst_max_ms = 1000;")

patch("kernel/sched/walt/sysctl.c",
      "\tsysctl_sched_group_downmigrate_pct = 95;",
      "\tsysctl_sched_group_downmigrate_pct = 85;")

# 3. Anti-Stutter: Watermark boost factor to 0 (no premature kswapd thrashing)
patch("mm/page_alloc.c",
      "int watermark_boost_factor __read_mostly = 15000;",
      "int watermark_boost_factor __read_mostly = 0;")

# 4. Networking: Bidirectional TCP Fast Open (Client + Server) out of the box
patch("net/ipv4/tcp_ipv4.c",
      "\tnet->ipv4.sysctl_tcp_fastopen = TFO_CLIENT_ENABLE;",
      "\tnet->ipv4.sysctl_tcp_fastopen = TFO_CLIENT_ENABLE | TFO_SERVER_ENABLE;")

# 5. Qualcomm Thermal Driver: Auto-disable charging thermal throttle
target_qti = "static int battery_psy_set_charge_current(struct battery_chg_dev *bcdev,\n\t\t\t\t\tint val)\n{"
replace_qti = """static int battery_psy_set_charge_current(struct battery_chg_dev *bcdev,
					int val)
{
	/* Carbon Kernel: Auto-disable charging thermal throttle */
	val = 0;"""
patch("drivers/power/supply/qti_battery_charger.c", target_qti, replace_qti)

# 6. Xiaomi Battmngr: Automatically disable THERMAL_DAEMON_VOTER on charge
target_thm = "int xm_charger_thermal(struct xm_charger *charger)\n{"
replace_thm = """int xm_charger_thermal(struct xm_charger *charger)
{
	/* Carbon Kernel: Automatically disable charging thermal throttling.
	 * THERMAL_DAEMON_VOTER is permanently disabled so fast charging never drops to 2W.
	 */
	charger->system_temp_level = 0;
	if (charger->fcc_votable) {
		vote(charger->fcc_votable, THERMAL_DAEMON_VOTER, false, 0);
		rerun_election(charger->fcc_votable);
	}
	return 0;
}

static int __unused_xm_charger_thermal(struct xm_charger *charger)
{"""
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_thermal.c", target_thm, replace_thm)

# 7. Xiaomi Battmngr Core: Set disable_thermal = 1 by default
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_core.c",
      "\tg_battmngr_noti->misc_msg.disable_thermal = 0;",
      "\tg_battmngr_noti->misc_msg.disable_thermal = 1;")

# 8. Anti-Detection VFS Engine (Prevent Livin Mandiri / Bank / Momo / Zygisk detection)
with open("fs/Makefile", "a", encoding="utf-8") as f:
    f.write("\nobj-y += suspicious.o\n")
print("Appended suspicious.o to fs/Makefile!")

# 8a. fs/stat.c: Hook vfs_getattr
with open("fs/stat.c", "r", encoding="utf-8") as f:
    c = f.read()
if "#include <linux/suspicious.h>" not in c:
    c = "#include <linux/suspicious.h>\n" + c
target_stat = """int vfs_getattr(const struct path *path, struct kstat *stat,
		u32 request_mask, unsigned int query_flags)
{
	int retval;"""
replace_stat = """int vfs_getattr(const struct path *path, struct kstat *stat,
		u32 request_mask, unsigned int query_flags)
{
	int retval;

	if (is_suspicious_path(path))
		return -ENOENT;"""
if target_stat in c:
    c = c.replace(target_stat, replace_stat, 1)
with open("fs/stat.c", "w", encoding="utf-8") as f:
    f.write(c)
print("Patched fs/stat.c with suspicious hook!")

# 8b. fs/namei.c: Hook do_filp_open
with open("fs/namei.c", "r", encoding="utf-8") as f:
    c = f.read()
if "#include <linux/suspicious.h>" not in c:
    c = "#include <linux/suspicious.h>\n" + c
target_namei = """struct file *do_filp_open(int dfd, struct filename *pathname,
		const struct open_flags *op)
{
	struct nameidata nd;
	int flags = op->lookup_flags;
	struct file *filp;"""
replace_namei = """struct file *do_filp_open(int dfd, struct filename *pathname,
		const struct open_flags *op)
{
	struct nameidata nd;
	int flags = op->lookup_flags;
	struct file *filp;

	if (suspicious_path(pathname))
		return ERR_PTR(-ENOENT);"""
if target_namei in c:
    c = c.replace(target_namei, replace_namei, 1)
with open("fs/namei.c", "w", encoding="utf-8") as f:
    f.write(c)
print("Patched fs/namei.c with suspicious hook!")

# 8c. fs/open.c: Hook do_faccessat
with open("fs/open.c", "r", encoding="utf-8") as f:
    c = f.read()
if "#include <linux/suspicious.h>" not in c:
    c = "#include <linux/suspicious.h>\n" + c
target_open = """retry:
	res = user_path_at(dfd, filename, lookup_flags, &path);
	if (res)
		goto out;"""
replace_open = """retry:
	res = user_path_at(dfd, filename, lookup_flags, &path);
	if (res)
		goto out;

	if (is_suspicious_path(&path)) {
		path_put(&path);
		res = -ENOENT;
		goto out;
	}"""
if target_open in c:
    c = c.replace(target_open, replace_open, 1)
with open("fs/open.c", "w", encoding="utf-8") as f:
    f.write(c)
print("Patched fs/open.c with suspicious hook!")

# 8d. fs/proc_namespace.c: Hook show_vfsmnt, show_mountinfo, show_vfsstat
with open("fs/proc_namespace.c", "r", encoding="utf-8") as f:
    c = f.read()
if "#include <linux/suspicious.h>" not in c:
    c = "#include <linux/suspicious.h>\n" + c

target_vfsmnt = """static int show_vfsmnt(struct seq_file *m, struct vfsmount *mnt)
{
	struct proc_mounts *p = m->private;
	struct mount *r = real_mount(mnt);
	struct path mnt_path = { .dentry = mnt->mnt_root, .mnt = mnt };
	struct super_block *sb = mnt_path.dentry->d_sb;
	int err;"""
replace_vfsmnt = """static int show_vfsmnt(struct seq_file *m, struct vfsmount *mnt)
{
	struct proc_mounts *p = m->private;
	struct mount *r = real_mount(mnt);
	struct path mnt_path = { .dentry = mnt->mnt_root, .mnt = mnt };
	struct super_block *sb = mnt_path.dentry->d_sb;
	int err;

	if (is_suspicious_mount(mnt, &p->root)) {
		err = SEQ_SKIP;
		goto out;
	}"""
if target_vfsmnt in c:
    c = c.replace(target_vfsmnt, replace_vfsmnt, 1)

target_mntinfo = """static int show_mountinfo(struct seq_file *m, struct vfsmount *mnt)
{
	struct proc_mounts *p = m->private;
	struct mount *r = real_mount(mnt);
	struct super_block *sb = mnt->mnt_sb;
	struct path mnt_path = { .dentry = mnt->mnt_root, .mnt = mnt };
	int err;"""
replace_mntinfo = """static int show_mountinfo(struct seq_file *m, struct vfsmount *mnt)
{
	struct proc_mounts *p = m->private;
	struct mount *r = real_mount(mnt);
	struct super_block *sb = mnt->mnt_sb;
	struct path mnt_path = { .dentry = mnt->mnt_root, .mnt = mnt };
	int err;

	if (is_suspicious_mount(mnt, &p->root)) {
		err = SEQ_SKIP;
		goto out;
	}"""
if target_mntinfo in c:
    c = c.replace(target_mntinfo, replace_mntinfo, 1)

target_vfsstat = """static int show_vfsstat(struct seq_file *m, struct vfsmount *mnt)
{
	struct proc_mounts *p = m->private;
	struct mount *r = real_mount(mnt);
	struct path mnt_path = { .dentry = mnt->mnt_root, .mnt = mnt };
	struct super_block *sb = mnt_path.dentry->d_sb;
	int err;"""
replace_vfsstat = """static int show_vfsstat(struct seq_file *m, struct vfsmount *mnt)
{
	struct proc_mounts *p = m->private;
	struct mount *r = real_mount(mnt);
	struct path mnt_path = { .dentry = mnt->mnt_root, .mnt = mnt };
	struct super_block *sb = mnt_path.dentry->d_sb;
	int err;

	if (is_suspicious_mount(mnt, &p->root)) {
		err = SEQ_SKIP;
		goto out;
	}"""
if target_vfsstat in c:
    c = c.replace(target_vfsstat, replace_vfsstat, 1)

# Also patch SUSFS functions if they exist in proc_namespace.c (without re-declaring p or violating C99 declaration rules)
susfs_hook_target = """	if (r->mnt_id >= DEFAULT_KSU_MNT_ID)
		return 0;"""
susfs_hook_replace = """	if (is_suspicious_mount(mnt, &p->root))
		return 0;

	if (r->mnt_id >= DEFAULT_KSU_MNT_ID)
		return 0;"""
if susfs_hook_target in c:
    # Replace both occurrences in susfs_show_vfsmnt and susfs_show_mountinfo
    c = c.replace(susfs_hook_target, susfs_hook_replace)

with open("fs/proc_namespace.c", "w", encoding="utf-8") as f:
    f.write(c)
print("Patched fs/proc_namespace.c with suspicious mount filters cleanly!")

print("All Carbon Kernel v1.4 Phoenix A tweaks & Anti-Detection hooks applied successfully!")
