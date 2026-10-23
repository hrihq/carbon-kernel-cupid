import sys

def patch(filepath, old, new):
    with open(filepath, 'r') as f:
        c = f.read()
    if old not in c:
        print(f"ERROR: {old[:40]} not found in {filepath}")
        sys.exit(1)
    with open(filepath, 'w') as f:
        f.write(c.replace(old, new, 1))
    print(f"Patched {filepath} successfully!")

# 1. WALT Scheduler: Scroll Cooling (keep light tasks on Little A510 cores)
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

# 3. Qualcomm Driver Legacy Fallback (qti_battery_charger.c)
patch("drivers/power/supply/qti_battery_charger.c",
      """	if (val < 0 || val >= bcdev->num_thermal_levels)
		return -EINVAL;""",
      """	if (val < 0 || val >= bcdev->num_thermal_levels)
		return -EINVAL;

	/* Carbon Kernel: Prevent charging current from collapsing to 2W */
	if (bcdev->num_thermal_levels > 4 && val > (bcdev->num_thermal_levels / 2))
		val = bcdev->num_thermal_levels / 2;""")

# 4. REAL XIAOMI CHARGER HARDWARE FLOOR (xm_charger_votable.c)
# This overrides the final effective FCC & ICL sent to the PMIC hardware!
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_votable.c",
      """	if (g_battmngr_noti->mainchg_msg.sw_disable)
		value = MAIN_MIN_FCC;

	ret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
					 MAIN_CHARGER_CURRENT, value / 1000);""",
      """	if (g_battmngr_noti->mainchg_msg.sw_disable)
		value = MAIN_MIN_FCC;

	/* Carbon Kernel: Anti-2W FCC floor (clamp minimum to 2500mA / 2.5A) */
	if (value > 0 && value < 2500000)
		value = 2500000;

	ret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
					 MAIN_CHARGER_CURRENT, value / 1000);""")

patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_votable.c",
      """	charger_err("%s: vote ICL = %d\n", __func__, value);
	ret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
					 MAIN_CHARGER_INPUT_CURRENT_SETTLED,
					 value / 1000);""",
      """	charger_err("%s: vote ICL = %d\n", __func__, value);

	/* Carbon Kernel: Anti-2W ICL floor (clamp minimum input to 2500mA / 2.5A) */
	if (value > 0 && value < 2500000)
		value = 2500000;

	ret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
					 MAIN_CHARGER_INPUT_CURRENT_SETTLED,
					 value / 1000);""")

# 5. REAL XIAOMI THERMAL DAEMON ENGINE (xm_charger_thermal.c)
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_thermal.c",
      """	} else {
		if (thermal_fcc_ua > 0) {
			rc = vote(charger->fcc_votable, THERMAL_DAEMON_VOTER,
				  true, thermal_fcc_ua);""",
      """	} else {
		if (thermal_fcc_ua > 0) {
			/* Carbon Kernel: Anti-2W thermal daemon floor (minimum 2.5A) */
			if (thermal_fcc_ua < 2500000)
				thermal_fcc_ua = 2500000;

			rc = vote(charger->fcc_votable, THERMAL_DAEMON_VOTER,
				  true, thermal_fcc_ua);""")

# 6. REAL XIAOMI JEITA BATTERY TEMP MONITOR (step-chg-jeita.c)
patch("drivers/power/supply/xiaomi/battmngr/charger/main/step-chg-jeita.c",
      """		vote(chip->fcc_votable, JEITA_VOTER, fcc_ua ? true : false,
		     fcc_ua);""",
      """		/* Carbon Kernel: Anti-2W JEITA floor (minimum 2.5A) */
		if (fcc_ua > 0 && fcc_ua < 2500000)
			fcc_ua = 2500000;

		vote(chip->fcc_votable, JEITA_VOTER, fcc_ua ? true : false,
		     fcc_ua);""")

print("All surgical Carbon Kernel v1.3 Xiaomi charging tweaks configured successfully!")
