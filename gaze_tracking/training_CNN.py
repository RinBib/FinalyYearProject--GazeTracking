import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# ✅ Use GPU if available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ✅ Define AI Model for Cognitive Decline Prediction
class CognitiveDeclineModel(nn.Module):
    def __init__(self):
        super(CognitiveDeclineModel, self).__init__()
        self.fc1 = nn.Linear(7, 64)  # 7 input features from gaze data
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 2)  # Binary classification (0: Healthy, 1: Cognitive Decline)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)  # No softmax (handled by CrossEntropyLoss)
        return x

# ✅ Load & Preprocess Data
def load_data(csv_file):
    df = pd.read_csv(csv_file)

    # ✅ Handle missing values
    df.fillna(0, inplace=True)

    required_columns = ["Speed_mm_per_sec", "Fixation_Detected", "fixation_duration",
                        "Blink_Count", "Blink_Duration", "Saccade_Count", "Saccade_Duration", "Cognitive_Decline_Label"]

    for col in required_columns:
        if col not in df.columns:
            print(f"[ERROR] Missing column: {col}. Cannot proceed with training.")
            return None, None, None, None

    # ✅ Extract features & labels
    X = df[["Speed_mm_per_sec", "Fixation_Detected", "fixation_duration",
            "Blink_Count", "Blink_Duration", "Saccade_Count", "Saccade_Duration"]].values
    y = df["Cognitive_Decline_Label"].values  # Labels: 0 (Healthy) or 1 (Decline)

    return train_test_split(X, y, test_size=0.2, random_state=42)

# ✅ Train Model
def train_model(csv_file, epochs=50, learning_rate=0.001):
    X_train, X_test, y_train, y_test = load_data(csv_file)

    if X_train is None:
        print("[ERROR] Training failed due to missing data.")
        return None

    # ✅ Convert data to PyTorch tensors
    X_train, X_test = torch.tensor(X_train, dtype=torch.float32).to(DEVICE), torch.tensor(X_test, dtype=torch.float32).to(DEVICE)
    y_train, y_test = torch.tensor(y_train, dtype=torch.long).to(DEVICE), torch.tensor(y_test, dtype=torch.long).to(DEVICE)

    model = CognitiveDeclineModel().to(DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    # ✅ Training loop
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0:
            print(f"Epoch {epoch}/{epochs}, Loss: {loss.item():.4f}")

    print("✅ Training Complete!")

    # ✅ Save Model
    torch.save(model.state_dict(), "cognitive_decline_model.pth")
    print("✅ Model saved as 'cognitive_decline_model.pth'")

    # ✅ Evaluate on Test Set
    with torch.no_grad():
        test_outputs = model(X_test)
        test_preds = torch.argmax(test_outputs, dim=1)
        accuracy = (test_preds == y_test).sum().item() / len(y_test)

    print(f"✅ Test Accuracy: {accuracy * 100:.2f}%")

    return model

# ✅ Run Training
if __name__ == "__main__":
    model = train_model("cognitive_decline_dataset.csv")
