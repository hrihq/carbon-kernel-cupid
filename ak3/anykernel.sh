properties() { '
kernel.string=Carbon Kernel for Xiaomi 12 (cupid)
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=cupid
supported.versions=
supported.patchlevels=
'; }

BLOCK=boot;
IS_SLOT_DEVICE=auto;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;

. tools/ak3-core.sh;

backup_current_boot() {
  backup_dir="/sdcard/carbon-kernel-backup";
  slot_name="${SLOT:-noslot}";
  stamp="$(date +%Y%m%d-%H%M%S 2>/dev/null || date +%s)";
  backup_img="${backup_dir}/boot-carbon-${slot_name}-${stamp}.img";
  backup_txt="${backup_dir}/boot-carbon-${slot_name}-${stamp}.txt";

  ui_print " ";
  ui_print "Backing up current boot image...";
  mkdir -p "$backup_dir" || abort "Unable to create ${backup_dir}. Aborting...";

  if [ ! -s "$BOOTIMG" ]; then
    abort "Dumped boot image is missing. Backup failed; aborting for safety.";
  fi;

  cp -f "$BOOTIMG" "$backup_img" || abort "Unable to save boot backup. Aborting...";
  {
    echo "device=cupid";
    echo "slot=${slot_name}";
    echo "source_block=${BLOCK}";
    echo "created=${stamp}";
    echo "backup=${backup_img}";
  } > "$backup_txt" 2>/dev/null || true;

  ui_print "Backup saved:";
  ui_print "  ${backup_img}";
}

ui_print " ";
ui_print "Carbon Kernel - Xiaomi 12 (cupid)";
ui_print "Current boot image will be backed up before flashing.";

split_boot;
backup_current_boot;
flash_boot;
