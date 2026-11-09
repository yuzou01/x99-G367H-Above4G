@echo -off
fs0:
echo "==== ROLLBACK: restore original Setup var ===="
dmpstore -all -l FS0:\efidump\setup_orig.bin
echo "==== verify (setup_orig = 158B) ===="
dmpstore Setup -guid EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9 -s FS0:\efidump\verify_rollback.bin
dir FS0:\efidump\verify_rollback.bin
echo "Restored. Power off, pull stick."
