import glob
import os

print("Current directory:", os.getcwd())

print("\nLooking for evie3 files...")
evie3_files = glob.glob("evie3/evie3_speed_test_*.csv")
print(evie3_files)

print("\nLooking for evie4 files...")
evie4_files = glob.glob("evie4/evie4_speed_test_*.csv")
print(evie4_files)
