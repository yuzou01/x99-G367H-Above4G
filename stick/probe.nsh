@echo -off
fs0:
echo "=========================================="
echo " G367H BIOS PROBE v7"
echo "=========================================="
mkdir FS0:\efidump
echo "==== SECTION A: NB fence regs (PHOTO) ===="
mm 0000000000100 -pcie -w 4
mm 0000000000104 -pcie -w 4
mm 0000000000108 -pcie -w 4
mm 000000000010c -pcie -w 4
mm 0000000000188 -pcie -w 4
mm 000000000018c -pcie -w 4
mm 0000000000190 -pcie -w 4
mm 0000000000194 -pcie -w 4
mm 00000000001a0 -pcie -w 4
echo "==== SECTION B: host bridge (PHOTO) ===="
pci 0 0 0 -i
echo "==== SECTION C: memory map (PHOTO) ===="
memmap
echo "==== writes ===="
dmpstore -all -s FS0:\efidump\vars_all.bin
dmpstore IntelSetup -s FS0:\efidump\var_intelsetup.bin
dmpstore Setup -s FS0:\efidump\var_setup.bin
dmpstore BootOrder -s FS0:\efidump\var_bootorder.bin
pci > FS0:\efidump\pcitree.txt
memmap > FS0:\efidump\memmap.txt
smbiosview > FS0:\efidump\smbios.txt
ver > FS0:\efidump\ver.txt
dmpstore -all > FS0:\efidump\vars_all.txt
echo "=========================================="
echo " DONE. dir listing below."
echo " If files listed: power off, pull stick."
echo " If NOT: photograph A, B, C first!"
echo "=========================================="
dir FS0:\efidump
