import pandas as pd
import glob

# Uses glob to find all relevant files
file_paths = sorted(glob.glob("deterministic_model_test/evie3/evie3_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evie4/evie4_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evie5/evie5_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evie6/evie6_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evie7/evie7_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evie8/evie8_speed_test_*.csv"))

print("Files found:", file_paths)

processed_data = []

for path in file_paths:
    df = pd.read_csv(path)
    df["Subject_ID"] = "john"
    df["Condition"] = "dementia"
    df = df.dropna(subset=["Left_Pupil_X", "Right_Pupil_X", "Speed_mm_per_sec"])
    processed_data.append(df)

if processed_data:
    final_df = pd.concat(processed_data, ignore_index=True)
    final_df.to_csv("john_cleaned_combined.csv", index=False)
    print(" Cleaned dataset saved as 'john_cleaned_combined.csv'")
else:
    print(" No valid files found to process.")
