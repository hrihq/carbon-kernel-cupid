properties() { '
kernel.string=Carbon Kernel for Xiaomi 12 (cupid)
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=cupid
device.name2=2201123G
device.name3=2201123C
device.name4=2201123E
supported.versions=
supported.patchlevels=
'; }

BLOCK=boot;
IS_SLOT_DEVICE=1;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=auto;

. tools/ak3-core.sh;

ui_print " ";
ui_print "Carbon Kernel - Xiaomi 12 (cupid)";

split_boot;
flash_boot;
