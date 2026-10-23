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
      "\tif (val < 0 || val >= bcdev->num_thermal_levels)\n\t\treturn -EINVAL;",
      "\tif (val < 0 || val >= bcdev->num_thermal_levels)\n\t\treturn -EINVAL;\n\n\tif (bcdev->num_thermal_levels > 4 && val > (bcdev->num_thermal_levels / 2))\n\t\tval = bcdev->num_thermal_levels / 2;")

# 4. Xiaomi xm_charger_votable.c - FCC Hard Hardware Floor
target_fcc = """\tif (g_battmngr_noti->mainchg_msg.sw_disable)
\t\tvalue = MAIN_MIN_FCC;

\tret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
\t\t\t\t\t MAIN_CHARGER_CURRENT, value / 1000);"""

replace_fcc = """\tif (g_battmngr_noti->mainchg_msg.sw_disable)
\t\tvalue = MAIN_MIN_FCC;

\t/* Carbon Kernel: Anti-2W FCC floor (clamp minimum to 2500mA / 2.5A) */
\tif (value > 0 && value < 2500000)
\t\tvalue = 2500000;

\tret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
\t\t\t\t\t MAIN_CHARGER_CURRENT, value / 1000);"""
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_votable.c", target_fcc, replace_fcc)

# 5. Xiaomi xm_charger_votable.c - ICL Hard Hardware Floor
target_icl = """\tret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
\t\t\t\t\t MAIN_CHARGER_INPUT_CURRENT_SETTLED,
\t\t\t\t\t value / 1000);"""

replace_icl = """\t/* Carbon Kernel: Anti-2W ICL floor (clamp minimum input to 2500mA / 2.5A) */
\tif (value > 0 && value < 2500000)
\t\tvalue = 2500000;

\tret = xm_battmngr_write_iio_prop(g_battmngr_iio, MAIN_CHG,
\t\t\t\t\t MAIN_CHARGER_INPUT_CURRENT_SETTLED,
\t\t\t\t\t value / 1000);"""
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_votable.c", target_icl, replace_icl)

# 6. Xiaomi xm_charger_thermal.c - Daemon Floor
target_thm = """\t} else {
\t\tif (thermal_fcc_ua > 0) {
\t\t\trc = vote(charger->fcc_votable, THERMAL_DAEMON_VOTER,
\t\t\t\t  true, thermal_fcc_ua);"""

replace_thm = """\t} else {
\t\tif (thermal_fcc_ua > 0) {
\t\t\t/* Carbon Kernel: Anti-2W thermal daemon floor (minimum 2.5A) */
\t\t\tif (thermal_fcc_ua < 2500000)
\t\t\t\tthermal_fcc_ua = 2500000;

\t\t\trc = vote(charger->fcc_votable, THERMAL_DAEMON_VOTER,
\t\t\t\t  true, thermal_fcc_ua);"""
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_thermal.c", target_thm, replace_thm)

# 7. Xiaomi step-chg-jeita.c - JEITA Temperature Floor
target_jeita = """\t\tvote(chip->fcc_votable, JEITA_VOTER, fcc_ua ? true : false,
\t\t     fcc_ua);"""

replace_jeita = """\t\t/* Carbon Kernel: Anti-2W JEITA floor (minimum 2.5A) */
\t\tif (fcc_ua > 0 && fcc_ua < 2500000)
\t\t\tfcc_ua = 2500000;

\t\tvote(chip->fcc_votable, JEITA_VOTER, fcc_ua ? true : false,
\t\t     fcc_ua);"""
patch("drivers/power/supply/xiaomi/battmngr/charger/main/step-chg-jeita.c", target_jeita, replace_jeita)

print("All surgical Carbon Kernel v1.3 Xiaomi charging tweaks configured successfully!")
