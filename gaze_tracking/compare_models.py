import os
import torch
from ai_model import process_gaze_data
from train_ai_model import CognitiveDeclineModel

# ✅ Use GPU if available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def compare_models(csv_file):
    """Compare AI model vs. deterministic method."""
    
    # ✅ Extract gaze tracking features
    gaze_data = process_gaze_data(csv_file)

    # ✅ Convert features to tensor
    X = torch.tensor(list(gaze_data.values()), dtype=torch.float32).unsqueeze(0).to(DEVICE)

    # ✅ Load trained AI model
    model_path = "cognitive_decline_model.pth"
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file '{model_path}' not found! Train the model first.")
        return
    
    model = CognitiveDeclineModel().to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()

    # ✅ AI Prediction
    with torch.no_grad():
        prediction = model(X)
        ai_result = torch.argmax(prediction).item()

    # ✅ Deterministic Model Prediction
    if (gaze_data["avg_speed"] < 5 and gaze_data["fixation_count"] < 50 and 
        gaze_data["avg_blink_duration"] > 400 and gaze_data["saccade_count"] < 5):
        deterministic_result = "Cognitive Decline"
    else:
        deterministic_result = "Healthy"

    # ✅ Print Results
    print(f"AI Model Prediction: {'Cognitive Decline' if ai_result == 1 else 'Healthy'}")
    print(f"Deterministic Model Prediction: {deterministic_result}")

if __name__ == "__main__":
    compare_models("deterministic_model_test/sample_gaze.csv")
