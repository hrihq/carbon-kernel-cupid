#!/sbin/sh

### AnyKernel3 Ramdisk Mod Script
## osm0sis @ xda-developers

### AnyKernel setup
properties() { '
kernel.string=Carbon Kernel for Xiaomi 12 (cupid)
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=cupid
device.name2=2201123G
device.name3=2201123C
device.name4=2201123E
supported.versions=
supported.patchlevels=
'; }

### AnyKernel install
attributes() {
  set_perm_recursive 0 0 755 644 $RAMDISK/*
  set_perm_recursive 0 0 750 750 $RAMDISK/init* $RAMDISK/sbin
  chmod 755 $AKHOME/tools/keycheck 2>/dev/null
}

BLOCK=boot
IS_SLOT_DEVICE=1
RAMDISK_COMPRESSION=auto
PATCH_VBMETA_FLAG=auto

. tools/ak3-core.sh

attributes

ui_print " "
if [ -f "$AKHOME/banner" ]; then
  cat "$AKHOME/banner"
fi
ui_print " "

ui_print "[1/3] Dumping boot image..."
split_boot

ui_print "[2/3] Flashing Carbon Kernel..."
flash_boot

ui_print "[3/3] Finalizing..."
ui_print " "
ui_print "========================================="
ui_print " Carbon Kernel installation completed!"
ui_print " Codename   : Sagittarius A*"
ui_print " Please reboot your device."
ui_print "========================================="
ui_print " "
