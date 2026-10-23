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

# 3. Charging Floor: Prevent dropping to 500mA (2W)
patch("drivers/power/supply/qti_battery_charger.c",
      """	if (val < 0 || val >= bcdev->num_thermal_levels)
		return -EINVAL;""",
      """	if (val < 0 || val >= bcdev->num_thermal_levels)
		return -EINVAL;

	/* Carbon Kernel: Prevent charging current from collapsing to 2W (500mA) */
	if (bcdev->num_thermal_levels > 4 && val > (bcdev->num_thermal_levels / 2))
		val = bcdev->num_thermal_levels / 2;""")

print("All Carbon v1.2 tweaks verified and applied!")
