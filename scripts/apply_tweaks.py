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

print("All Carbon Kernel v1.4 Phoenix A tweaks applied successfully!")
