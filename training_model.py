import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from CNN_LSTM_model import create_cnn_lstm_model


# Load your CSV files containing gaze data from impaired and healthy subjects
# # demented subject
john_df = pd.read_csv("cleaned_extracted_data\john_cleaned_combined.csv") 
 # healthy subject
evangel_df = pd.read_csv("cleaned_extracted_data\evangeline_cleaned_combined.csv") 

# Add labels for classification (supervised learning)
john_df["label"] = "impaired"
evangel_df["label"] = "healthy"

# Combine the datasets and shuffle 
data_df = pd.concat([john_df, evangel_df], ignore_index=True)
# Drop missing data and shuffle
data_df = data_df.dropna().sample(frac=1).reset_index(drop=True) 

# Define which columns 
# These include eye speed, pupil coordinates, and movement indicators like blinks and saccades
features = [
    'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
    'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
    'fixation_duration', 'Blink_Count', 'Blink_Duration',
    'Saccade_Count', 'Saccade_Duration'
]

# Extract feature values and label column
df_features = data_df[features]
X = df_features.values  
y = data_df['label'].values

# Convert text labels to binary 
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Normalize all input features using standard scaling (mean=0, std=1)
# This is very important for neural networks to converge properly
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Segment the gaze data into sequences for LSTM input
# Each sequence will contain 20 consecutive frames 
# 20 frames at 30 FPS = 0.6 seconds of tracking
# This is long enough to capture temporal patterns like fixations, blinks, or saccades
# 10–30 time steps is good for short behavioral sequences in LSTMs
window_size = 20
X_seq = np.array([X_scaled[i:i+window_size] for i in range(len(X_scaled) - window_size + 1)])
y_seq = np.array([y_encoded[i + window_size - 1] for i in range(len(X_scaled) - window_size + 1)])

# Split into training and testing sets 80 20
X_train, X_test, y_train, y_test = train_test_split(X_seq, y_seq, test_size=0.2, random_state=42)

# Create the model
model = create_cnn_lstm_model(window_size=window_size, num_features=len(features))

model.summary()  # Show model architecture

# Train the model for 20 epochs using batch size of 32
# You can increase epochs if needed for better results
model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=20,
    batch_size=32,
    verbose=1
)

# Save the trained model as an HDF5 file for later use
model.save("cognitive_classifier_model.h5")
print("Model trained and saved as cognitive_classifier_model.h5")
