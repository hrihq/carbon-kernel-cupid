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

DEVICE="$(getprop ro.product.device 2>/dev/null)"
[ -z "$DEVICE" ] && DEVICE="Unknown"

SLOT_NAME="${SLOT#_}"
[ -z "$SLOT_NAME" ] && SLOT_NAME="N/A"

ui_print "Device : $DEVICE"
ui_print "Slot   : $SLOT_NAME"
ui_print " "

case "$DEVICE" in
    cupid|2201123G|2201123C|2201123E)
        ui_print "Supported device detected."
        ;;
    *)
        ui_print "Unsupported device: $DEVICE"
        abort "Installation aborted."
        ;;
esac

ui_print " "

check_and_clean_root_residue() {
    mount /data 2>/dev/null
    if [ -d "/data/adb" ]; then
        ui_print "========================================="
        ui_print "        Root Residue Detected!"
        ui_print "========================================="
        ui_print " Found leftover root files in /data/adb"
        ui_print " Clean root residue for banking safety?"
        ui_print " "
        ui_print " [Vol UP (+)]   : Yes, Wipe /data/adb"
        ui_print " [Vol DOWN (-)] : No, Keep /data/adb"
        ui_print "-----------------------------------------"
        ui_print " Default (10s)  : Yes, Wipe /data/adb"
        ui_print "========================================="
        ui_print " "

        clean_key=0
        chmod 755 "$AKHOME/tools/keycheck" 2>/dev/null
        if [ -x "$AKHOME/tools/keycheck" ]; then
            "$AKHOME/tools/keycheck" 10
            clean_key=$?
        elif which getevent >/dev/null 2>&1; then
            timeout 10 sh -c '
                while true; do
                    line=$(getevent -lqc 1 2>/dev/null)
                    case "$line" in
                        *KEY_VOLUMEUP*DOWN*|*KEY_VOLUMEUP*0001*|*0073*00000001*) exit 42 ;;
                        *KEY_VOLUMEDOWN*DOWN*|*KEY_VOLUMEDOWN*0001*|*0072*00000001*) exit 41 ;;
                    esac
                done' 2>/dev/null
            clean_key=$?
        fi

        if [ "$clean_key" -eq 41 ]; then
            ui_print "-> Kept /data/adb residue."
        else
            rm -rf /data/adb
            ui_print "-> /data/adb wiped clean."
        fi
        ui_print " "
    fi
}

CHOSEN_VARIANT="Root (KernelSU-Next + SuSFS)"
CHOSEN_KSUN="v3.4.2"
CHOSEN_SUSFS="v2.3.0"

if [ -f "$AKHOME/kernels/Image-root" ] && [ -f "$AKHOME/kernels/Image-nonroot" ]; then
    ui_print "========================================="
    ui_print "       Select Kernel Variant"
    ui_print "========================================="
    ui_print " [Vol UP (+)]   : Root (KernelSU-Next + SuSFS)"
    ui_print " [Vol DOWN (-)] : Non-Root (Clean / Stock)"
    ui_print "-----------------------------------------"
    ui_print " Press Volume Key now (10s timeout)..."
    ui_print " Default: Root (KernelSU-Next + SuSFS)"
    ui_print "========================================="
    ui_print " "

    KEY_RESULT=0
    chmod 755 "$AKHOME/tools/keycheck" 2>/dev/null
    if [ -x "$AKHOME/tools/keycheck" ]; then
        "$AKHOME/tools/keycheck" 10
        KEY_RESULT=$?
    elif which getevent >/dev/null 2>&1; then
        timeout 10 sh -c '
            while true; do
                line=$(getevent -lqc 1 2>/dev/null)
                case "$line" in
                    *KEY_VOLUMEUP*DOWN*|*KEY_VOLUMEUP*0001*|*0073*00000001*) exit 42 ;;
                    *KEY_VOLUMEDOWN*DOWN*|*KEY_VOLUMEDOWN*0001*|*0072*00000001*) exit 41 ;;
                esac
            done' 2>/dev/null
            KEY_RESULT=$?
    fi

    if [ "$KEY_RESULT" -eq 41 ]; then
        ui_print "-> Selected: Non-Root (Clean / Stock)"
        cp -f "$AKHOME/kernels/Image-nonroot" "$AKHOME/Image"
        CHOSEN_VARIANT="Non-Root (Clean / Stock)"
        CHOSEN_KSUN="Disabled"
        CHOSEN_SUSFS="Disabled"
        check_and_clean_root_residue
    else
        if [ "$KEY_RESULT" -eq 42 ]; then
            ui_print "-> Selected: Root (KernelSU-Next + SuSFS)"
        else
            ui_print "-> Timeout / No input. Default: Root"
        fi
        cp -f "$AKHOME/kernels/Image-root" "$AKHOME/Image"
        CHOSEN_VARIANT="Root (KernelSU-Next + SuSFS)"
    fi
elif [ -f "$AKHOME/kernels/Image-root" ]; then
    cp -f "$AKHOME/kernels/Image-root" "$AKHOME/Image"
elif [ -f "$AKHOME/kernels/Image-nonroot" ]; then
    cp -f "$AKHOME/kernels/Image-nonroot" "$AKHOME/Image"
    CHOSEN_VARIANT="Non-Root (Clean / Stock)"
    CHOSEN_KSUN="Disabled"
    CHOSEN_SUSFS="Disabled"
    check_and_clean_root_residue
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
ui_print " Variant    : $CHOSEN_VARIANT"
ui_print " KernelSU-N : $CHOSEN_KSUN"
ui_print " SuSFS      : $CHOSEN_SUSFS"
ui_print " Please reboot your device."
ui_print "========================================="
ui_print " "
