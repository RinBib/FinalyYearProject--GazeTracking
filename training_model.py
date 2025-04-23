# pyright: reportMissingImports=false
# pyright: reportMissingModuleSource=false
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
from sklearn.metrics import classification_report


model = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
# Load your CSV files containing gaze data from impaired and healthy subjects
# # demented subject
john_df = pd.read_csv("cleaned_extracted_data\john_cleaned_combined.csv") 
 # healthy subject
cat_df = pd.read_csv("cleaned_extracted_data\cat_cleaned_combined.csv") 




# Add labels for classification (supervised learning)
john_df["label"] = "impaired"
cat_df["label"] = "healthy"

# Combine the datasets and shuffle 
data_df = pd.concat([john_df, cat_df], ignore_index=True)
# Drop missing data and shuffle
data_df = data_df.dropna().sample(frac=1).reset_index(drop=True) 

# Define which columns 
# These include eye speed, pupil coordinates, and movement indicators like blinks and saccades
features = [
    'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
    'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
    'fixation_duration', 'Blink_Count', 'Blink_Duration']
    #'Saccade_Count', 'Saccade_Duration']

X = data_df[features].values
y = data_df['label'].values

# 5. Encode labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)  # 0 = impaired, 1 = healthy

# 6. Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 7. Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

model = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
model.fit(X_train, y_train)

# 9. model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f" Random Forest Test Accuracy: {accuracy * 100:.2f}%")

# 10. Save the model and scaler
joblib.dump(model, "model.joblib")
joblib.dump(scaler, "scaler.pkl")
print(" Model saved as model.joblib and scaler.pkl")



# Load your test features and labels (not new real-world data — use training or validation data)
X_test_scaled = scaler.transform(X_test)
y_pred = model.predict(X_test_scaled)  

print(classification_report(y_test, y_pred))
