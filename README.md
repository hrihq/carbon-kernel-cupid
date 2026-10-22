# Carbon Kernel - Xiaomi 12 (cupid)

Custom GKI Linux 5.10 Kernel with **KernelSU-Next** integration for **Xiaomi 12 (`cupid` / Qualcomm SM8450 Snapdragon 8 Gen 1)** running LineageOS 24 (or AOSP/crDroid-based ROMs).

## Features
- **Kernel Base**: Upstream `LineageOS/android_kernel_xiaomi_sm8450` (Linux 5.10 GKI, branch `lineage-24.0`).
- **Target Device**: Xiaomi 12 (`cupid`).
- **Root Solution**: [KernelSU-Next](https://github.com/KernelSU-Next/KernelSU-Next) (branch `next`).
- **Branding**: `-Carbon-cupid` localversion.
- **Installer**: Flashable AnyKernel3 ZIP with auto boot backup (`/sdcard/carbon-kernel-backup`).

## How to Build via GitHub Actions
1. Go to the **Actions** tab on this repo.
2. Select **Build Carbon Kernel (cupid)**.
3. Click **Run workflow** (default: `ksu_variant: next`, `lto: thin`).
4. Wait for the build to complete, then download the ZIP artifact or check **Releases**.

## How to Flash
1. Download `Carbon-Kernel-cupid-next-r<build>.zip` from Releases.
2. Boot into recovery (TWRP / OrangeFox).
3. Flash the `.zip`.
4. Reboot system and install the latest **KernelSU-Next Manager APK**.
