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

# 2. Anti-Stutter: Watermark boost factor to 0 (no premature kswapd thrashing)
patch("mm/page_alloc.c",
      "int watermark_boost_factor __read_mostly = 15000;",
      "int watermark_boost_factor __read_mostly = 0;")

# 3. Qualcomm Thermal Driver: Auto-disable charging thermal throttle
target_qti = "static int battery_psy_set_charge_current(struct battery_chg_dev *bcdev,\n\t\t\t\t\tint val)\n{"
replace_qti = """static int battery_psy_set_charge_current(struct battery_chg_dev *bcdev,
					int val)
{
	/* Carbon Kernel: Auto-disable charging thermal throttle */
	val = 0;"""
patch("drivers/power/supply/qti_battery_charger.c", target_qti, replace_qti)

# 4. Xiaomi Battmngr: Automatically disable THERMAL_DAEMON_VOTER on charge
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

# 5. Xiaomi Battmngr Core: Set disable_thermal = 1 by default
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_core.c",
      "\tg_battmngr_noti->misc_msg.disable_thermal = 0;",
      "\tg_battmngr_noti->misc_msg.disable_thermal = 1;")

print("All Auto-Disable Charging Thermal Throttling tweaks applied successfully!")
