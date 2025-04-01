import pandas as pd
import glob

# Uses glob to find all relevant files
file_paths = sorted(#glob.glob("deterministic_model_test/cat3/cat3_speed_test_*.csv") +
                    #glob.glob("deterministic_model_test/cat4/cat4_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evangeline1/evangeline1_speed_test_*.csv") + 
                    glob.glob("deterministic_model_test/evangeline2/evangeline2_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evangeline3/evangeline3_speed_test_*.csv") +
                    glob.glob("deterministic_model_test/evangeline4/evangeline4_speed_test_*.csv"))

print("Files found:", file_paths)

processed_data = []

for path in file_paths:
    df = pd.read_csv(path)
    df["Subject_ID"] = "cat"
    df["Condition"] = "healthy"
    df = df.dropna(subset=["Left_Pupil_X", "Right_Pupil_X", "Speed_mm_per_sec"])
    processed_data.append(df)

if processed_data:
    final_df = pd.concat(processed_data, ignore_index=True)
    final_df.to_csv("evangeline_cleaned_combined.csv", index=False)
    print(" Cleaned dataset saved as 'cat_cleaned_combined.csv'")
else:
    print(" No valid files found to process.")
