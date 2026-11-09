@echo -off
fs0:
echo "=========================================="
echo " G367H r14 v10: Above 4G Decoding = 1"
echo " (Setup var offset 0x3A = THE real knob)"
echo "=========================================="
echo "==== [1/3] load setup_a4g.bin ===="
dmpstore -all -l FS0:\efidump\setup_a4g.bin
echo "==== [2/3] verify: re-save Setup var ===="
dmpstore Setup -guid EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9 -s FS0:\efidump\verify_setup.bin
dir FS0:\efidump\verify_setup.bin
echo "=========================================="
echo " verify_setup.bin should be 158 B."
echo " If yes: power OFF, pull stick, boot normal."
echo "=========================================="
