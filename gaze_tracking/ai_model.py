import numpy as np
import torch
import torch.nn as nn
from scipy.ndimage import zoom
from scipy.special import logsumexp
import cv2
import deepgaze_pytorch
import pandas as pd
# ✅ Use CUDA if available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ✅ Load DeepGazeIIE Model (uses EfficientNet-B5)
model = deepgaze_pytorch.DeepGazeIIE(pretrained=True).to(DEVICE)
model.eval()  # Set to evaluation mode

# ✅ Load precomputed center bias (download from DeepGaze repo if needed)
centerbias_template = np.load('centerbias_mit1003.npy')
centerbias = zoom(centerbias_template, (480/1024, 640/1024), order=0, mode='nearest')  # Resize for your input image
centerbias -= logsumexp(centerbias)  # Normalize

def process_image(image_path):
    """Load an image and preprocess it for DeepGazeIIE."""
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Could not load image: {image_path}")
        return None
    
    image = cv2.resize(image, (640, 480))  # Resize to match centerbias
    image_tensor = torch.tensor([image.transpose(2, 0, 1).astype(np.float32)], dtype=torch.float32).to(DEVICE)
    centerbias_tensor = torch.tensor([centerbias]).float().to(DEVICE)

    # ✅ Predict saliency map
    with torch.no_grad():
        log_density_prediction = model(image_tensor, centerbias_tensor)

    return log_density_prediction.cpu().numpy()


def process_gaze_data(csv_file):
    """Load gaze tracking data and convert it into a format suitable for DeepGazeIIE."""
    df = pd.read_csv(csv_file)
    
     # Handle missing columns safely
    required_columns = ["Speed_mm_per_sec", "Fixation_Detected", "fixation_duration",
                        "Blink_Count", "Blink_Duration", "Saccade_Count", "Saccade_Duration"]

    for col in required_columns:
        if col not in df.columns:
            print(f"[WARNING] Missing column: {col}. Filling with default values.")
            df[col] = 0  # Fill missing columns with 0

    # ✅ Extract relevant eye-tracking features
    gaze_features = {
        "avg_speed": df["Speed_mm_per_sec"].mean(),
        "fixation_count": df["Fixation_Detected"].sum(),
        "avg_fixation_duration": df["fixation_duration"].mean(),
        "blink_count": df["Blink_Count"].sum(),
        "avg_blink_duration": df["Blink_Duration"].mean(),
        "saccade_count": df["Saccade_Count"].sum(),
        "avg_saccade_duration": df["Saccade_Duration"].mean()
    }

    print(f"Extracted Features: {gaze_features}")
    return gaze_features



if __name__ == "__main__":
    print("🔹 Running AI Model with DeepGazeIIE & Eye-Tracking Data...")

    # ✅ Process Sample Image
    saliency_map = process_image("sample_image.jpg")
    if saliency_map is not None:
        print("✅ DeepGazeIIE Prediction Complete!")

    # ✅ Process Sample CSV
    gaze_data = process_gaze_data("deterministic_model_test/sample_gaze.csv")

    print("✅ Gaze Data Extraction Complete!")
