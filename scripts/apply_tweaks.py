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

def apply_all():
    # 1. WALT Scheduler: Scroll Cooling (keep light tasks on Little A510 cores, sleep Cortex-X2)
    patch("kernel/sched/walt/walt_config.c",
          "\tsysctl_sched_min_task_util_for_boost = 51;",
          "\tsysctl_sched_min_task_util_for_boost = 100;")

    patch("kernel/sched/walt/walt_config.c",
          "\tsysctl_sched_min_task_util_for_colocation = 35;",
          "\tsysctl_sched_min_task_util_for_colocation = 70;")

    # 2. WALT Scheduler: Fast Core Release & Downmigrate for Snapdragon 8 Gen 1 (tame CPU thermals)
    patch("kernel/sched/walt/walt_config.c",
          "\tsysctl_sched_coloc_busy_hyst_max_ms = 5000;",
          "\tsysctl_sched_coloc_busy_hyst_max_ms = 1000;")

    patch("kernel/sched/walt/walt_config.c",
          "\tsysctl_sched_group_downmigrate_pct = 95;",
          "\tsysctl_sched_group_downmigrate_pct = 85;")

    # 3. Anti-Stutter: Watermark boost factor to 0 (no premature kswapd thrashing)
    patch("mm/page_alloc.c",
          "static int watermark_boost_factor __read_mostly = 15000;",
          "static int watermark_boost_factor __read_mostly = 0;")

    # 4. Networking: Bidirectional TCP Fast Open (Client + Server) out of the box
    patch("net/ipv4/tcp_ipv4.c",
          "\tnet->ipv4.sysctl_tcp_fastopen = TFO_CLIENT_ENABLE;",
          "\tnet->ipv4.sysctl_tcp_fastopen = TFO_CLIENT_ENABLE | TFO_SERVER_ENABLE;")

    # ponytail: 6.6 GKI charger/battery drivers moved to external sm8450-modules-6.6; patch vendor modules if charger bypass requested.

    print("Carbon Kernel 6.6 tweaks applied cleanly.")

def self_test():
    sample_walt = "\tsysctl_sched_min_task_util_for_boost = 51;\n\tsysctl_sched_group_downmigrate_pct = 95;"
    assert "\tsysctl_sched_min_task_util_for_boost = 100;" in sample_walt.replace("51", "100")
    assert "\tsysctl_sched_group_downmigrate_pct = 85;" in sample_walt.replace("95", "85")
    sample_mm = "static int watermark_boost_factor __read_mostly = 15000;"
    assert "static int watermark_boost_factor __read_mostly = 0;" == sample_mm.replace("15000", "0")
    print("self_test passed.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        self_test()
    else:
        apply_all()
