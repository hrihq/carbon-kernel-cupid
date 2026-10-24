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

# 3. Qualcomm Driver: Ignore thermal throttle requests completely
target_qti = """static int battery_psy_set_charge_current(struct battery_chg_dev *bcdev,
					int val)
{
	int rc;
//	u32 fcc_ua, prev_fcc_ua;
	struct psy_state *pst = NULL;

	pst = &bcdev->psy_list[PSY_TYPE_XM];

	pr_info("set thermal-level: %d num_thermal_levels: %d \n", val, bcdev->num_thermal_levels);

	if (!bcdev->num_thermal_levels)
		return 0;

	if (bcdev->num_thermal_levels < 0) {
		pr_err("Incorrect num_thermal_levels\n");
		return -EINVAL;
	}

	if (val < 0 || val >= bcdev->num_thermal_levels)
		return -EINVAL;

	rc = write_property_id(bcdev, &bcdev->psy_list[PSY_TYPE_BATTERY],
				BATT_CHG_CTRL_LIM, val);
	if (rc < 0)
		pr_err("Failed to set ccl:%d, rc=%d\n", val, rc);

	bcdev->curr_thermal_level = val;

	pr_err("chg_type=%s tl:=%d  ffc:=%d, pd_verifed:=%d\n",get_usb_type_name(pst->prop[XM_PROP_REAL_TYPE]),
			bcdev->curr_thermal_level, pst->prop[XM_PROP_FASTCHGMODE], pst->prop[XM_PROP_PD_VERIFED]);

#if 0
	if (bcdev->thermal_fcc_step == 0)
		fcc_ua = bcdev->thermal_levels[val];
	else
		fcc_ua = bcdev->psy_list[PSY_TYPE_BATTERY].prop[BATT_CHG_CTRL_LIM_MAX]
				- (bcdev->thermal_fcc_step * val);

	prev_fcc_ua = bcdev->thermal_fcc_ua;
	bcdev->thermal_fcc_ua = fcc_ua;

	rc = __battery_psy_set_charge_current(bcdev, fcc_ua);
	if (!rc)
		bcdev->curr_thermal_level = val;
	else
		bcdev->thermal_fcc_ua = prev_fcc_ua;
#endif

	return rc;
}"""

replace_qti = """static int battery_psy_set_charge_current(struct battery_chg_dev *bcdev,
					int val)
{
	/* Carbon Kernel: Auto-disable charging thermal throttle */
	bcdev->curr_thermal_level = 0;
	return 0;
}"""
patch("drivers/power/supply/qti_battery_charger.c", target_qti, replace_qti)

# 4. Xiaomi Battmngr: Permanently disable THERMAL_DAEMON_VOTER on charge
target_thm = """int xm_charger_thermal(struct xm_charger *charger)
{
	int thermal_fcc_ua = 0;
	int rc = 0;

	if ((charger->system_temp_level >= MAX_TEMP_LEVEL) ||
	    (charger->system_temp_level < 0))
		return -EINVAL;

	switch (charger->real_type) {
	case POWER_SUPPLY_TYPE_USB_PD:
		if (charger->pd_active == QTI_POWER_SUPPLY_PD_PPS_ACTIVE) {
			thermal_fcc_ua = charger->dt.thermal_mitigation_pd_cp
						 [charger->system_temp_level];
		} else {
			thermal_fcc_ua = charger->dt.thermal_mitigation_pd
						 [charger->system_temp_level];
			g_battmngr_noti->misc_msg.thermal_icl =
				charger->dt.thermal_mitigation_icl
					[charger->system_temp_level];
		}
		break;
	default:
		if (charger->bc12_type == POWER_SUPPLY_TYPE_USB_HVDCP) {
			g_battmngr_noti->misc_msg.thermal_icl =
				charger->dt.thermal_mitigation_qc2
					[charger->system_temp_level];
		} else {
			thermal_fcc_ua = charger->dt.thermal_mitigation
						 [charger->system_temp_level];
			g_battmngr_noti->misc_msg.thermal_icl =
				charger->dt.thermal_mitigation_dcp
					[charger->system_temp_level];
		}

		break;
	}

	if (g_battmngr_noti->misc_msg.disable_thermal && charger->pd_active) {
		if (charger->pd_active == QTI_POWER_SUPPLY_PD_PPS_ACTIVE) {
			thermal_fcc_ua =
				charger->dt.thermal_mitigation_pd_cp[0];
		} else {
			thermal_fcc_ua = charger->dt.thermal_mitigation_pd[0];
		}
	}

	charger_err(
		"%s: chg->system_temp_level: %d, thermal_icl:%d, real_type:%d, thermal_fcc_ua is %d, pd_active = %d, bc12_type = %d\n",
		__func__, charger->system_temp_level,
		g_battmngr_noti->misc_msg.thermal_icl, charger->real_type,
		thermal_fcc_ua, charger->pd_active, charger->bc12_type);

	if (charger->system_temp_level == 0) {
		rc = vote(charger->fcc_votable, THERMAL_DAEMON_VOTER, false, 0);
		if (rc < 0)
			charger_err(
				"%s: Couldn't disable USB thermal FCC vote rc = %d\n",
				__func__, rc);
	} else {
		if (thermal_fcc_ua > 0) {
			rc = vote(charger->fcc_votable, THERMAL_DAEMON_VOTER,
				  true, thermal_fcc_ua);
			if (rc < 0)
				charger_err(
					"%s: Couldn't enable USB thermal FCC vote rc = %d\n",
					__func__, rc);
		}
	}
	rerun_election(charger->fcc_votable);

	return rc;
}"""

replace_thm = """int xm_charger_thermal(struct xm_charger *charger)
{
	/* Carbon Kernel: Automatically disable charging thermal throttling.
	 * THERMAL_DAEMON_VOTER is permanently disabled so fast charging never throttles.
	 */
	charger->system_temp_level = 0;
	if (charger->fcc_votable) {
		vote(charger->fcc_votable, THERMAL_DAEMON_VOTER, false, 0);
		rerun_election(charger->fcc_votable);
	}
	return 0;
}"""
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_thermal.c", target_thm, replace_thm)

# 5. Xiaomi Battmngr Core: Set disable_thermal = 1 by default
patch("drivers/power/supply/xiaomi/battmngr/charger/main/xm_charger_core.c",
      "\tg_battmngr_noti->misc_msg.disable_thermal = 0;",
      "\tg_battmngr_noti->misc_msg.disable_thermal = 1;")

print("All Auto-Disable Charging Thermal Throttling tweaks applied successfully!")
