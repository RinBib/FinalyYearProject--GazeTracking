import cv2
import numpy as np
import os
import csv
from datetime import datetime
import sys
import time  
import math  
import pandas as pd  # ✅ Added to process CSV data
import matplotlib.pyplot as plt

# Ensure Python can find 'gaze_tracking'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gaze_tracking import GazeTracking

# Initialize GazeTracking
gaze = GazeTracking()

# Constants for real-world conversion
DPI = 96  # Approximate DPI of a standard screen
SCREEN_DISTANCE_MM = 600  # Approximate screen distance in mm (adjust as needed)
PIXEL_TO_MM = 25.4 / DPI  # Conversion factor: Pixels to millimeters

def initialize_csv(log_file, headers):
    """Create the CSV file with headers."""
    with open(log_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

def log_data(log_file, data):
    """Log speed data to the CSV file."""
    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)

def pupils_located():
    """Check if pupils are detected before tracking."""
    try:
        int(gaze.eye_left.pupil.x)
        int(gaze.eye_left.pupil.y)
        int(gaze.eye_right.pupil.x)
        int(gaze.eye_right.pupil.y)
        return True
    except Exception:
        return False

def calculate_speed(prev_point, curr_point, prev_time, curr_time):
    """Calculate movement speed in pixels/sec, mm/sec, and degrees/sec."""
    distance_px = np.sqrt((curr_point[0] - prev_point[0])**2 + (curr_point[1] - prev_point[1])**2)
    time_diff = curr_time - prev_time
    if time_diff <= 0:
        return 0, 0, 0  # Avoid division by zero

    # ✅ Convert pixels to mm
    distance_mm = distance_px * PIXEL_TO_MM
    speed_mm_sec = distance_mm / time_diff

    # ✅ Convert mm to degrees of visual angle
    speed_deg_sec = 2 * math.degrees(math.atan(distance_mm / (2 * SCREEN_DISTANCE_MM))) / time_diff

    return distance_px / time_diff, speed_mm_sec, speed_deg_sec  

def get_next_filename(participant_name):
    """Find the next sequential file name for the patient session."""
    folder_path = f"deterministic_model_test/{participant_name}"
    os.makedirs(folder_path, exist_ok=True)  # ✅ Ensure folder exists

    existing_files = [f for f in os.listdir(folder_path) if f.startswith(f"{participant_name}_speed_test") and f.endswith(".csv")]
    next_number = len(existing_files) + 1  

    return f"{folder_path}/{participant_name}_speed_test_{next_number}.csv"

def track_eye_speed(participant_name, tracking_duration=10):
    """Run a 10-second test to measure eye movement speed with real-world units."""
    log_file = get_next_filename(participant_name)
    initialize_csv(log_file, ["Timestamp", "Left_Pupil_X", "Left_Pupil_Y",
                              "Right_Pupil_X", "Right_Pupil_Y", "Speed_px_per_sec", "Speed_mm_per_sec", "Speed_deg_per_sec"])

    webcam = cv2.VideoCapture(0)
    time.sleep(2)  

    if not webcam.isOpened():
        print("Error: Cannot access the webcam.")
        return

    print(f"Running speed test for {participant_name}... Test will stop automatically after 10 seconds.")

    prev_x, prev_y, prev_timestamp = None, None, None
    start_time = time.time()  

    while time.time() - start_time < tracking_duration:  
        _, frame = webcam.read()
        gaze.refresh(frame)

        if pupils_located():
            left_pupil = gaze.pupil_left_coords()
            right_pupil = gaze.pupil_right_coords()

            if left_pupil and right_pupil:
                timestamp = datetime.now().timestamp() * 1000  
                curr_x = (left_pupil[0] + right_pupil[0]) / 2
                curr_y = (left_pupil[1] + right_pupil[1]) / 2

                if prev_x is not None and prev_y is not None:
                    speed_px_sec, speed_mm_sec, speed_deg_sec = calculate_speed(
                        (prev_x, prev_y), (curr_x, curr_y), prev_timestamp, timestamp
                    )

                    log_data(log_file, [
                        datetime.now(), *left_pupil, *right_pupil, speed_px_sec, speed_mm_sec, speed_deg_sec
                    ])

                    cv2.putText(frame, f"Speed: {speed_mm_sec:.2f} mm/sec", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Speed: {speed_deg_sec:.2f} deg/sec", (50, 130),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                prev_x, prev_y = curr_x, curr_y
                prev_timestamp = timestamp

        remaining_time = int(tracking_duration - (time.time() - start_time))
        cv2.putText(frame, f"Time Left: {remaining_time} sec", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        frame = gaze.annotated_frame()
        cv2.imshow("Eye Speed Tracking", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  
            break

    webcam.release()
    cv2.destroyAllWindows()
    print(f"Speed test completed. Data saved to {log_file}")

    check_weekly_prediction(participant_name)

def check_weekly_prediction(participant_name):
    """After 7 days, generate a prediction based on speed trends."""
    folder_path = f"deterministic_model_test/{participant_name}"
    files = sorted([f for f in os.listdir(folder_path) if f.startswith(f"{participant_name}_speed_test") and f.endswith(".csv")])

    if len(files) < 7:
        print(f"Not enough data for {participant_name}. {len(files)}/7 sessions completed.")
        return

    speeds = []
    for file in files[-7:]:  
        df = pd.read_csv(os.path.join(folder_path, file))
        speeds.extend(df["Speed_mm_per_sec"].dropna().tolist())  

    avg_speed = np.mean(speeds)

    if avg_speed < 5:
        prediction = "Possible Fatigue / Slow Cognitive Response"
    elif 5 <= avg_speed <= 20:
        prediction = "Normal Eye Movement"
    else:
        prediction = "Possible Restlessness / Attention Issues"

    print(f"Prediction for {participant_name} after 7 days: {prediction}")
    
def plot_weekly_speed_trend(participant_name):
    """Generate a scatter plot of speed trends over 7 days."""
    folder_path = f"deterministic_model_test/{participant_name}"
    
    # Ensure folder exists
    if not os.path.exists(folder_path):
        print(f"Error: No data found for {participant_name}.")
        return
    
    files = sorted([f for f in os.listdir(folder_path) if f.startswith(f"{participant_name}_speed_test") and f.endswith(".csv")])

    if len(files) < 7:
        print(f"Not enough data for {participant_name}. {len(files)}/7 sessions completed.")
        return

    day_numbers = list(range(1, 8))
    avg_speeds = []

    for file in files[-7:]:  # Get the last 7 files
        df = pd.read_csv(os.path.join(folder_path, file))
        avg_speed = np.mean(df["Speed_mm_per_sec"].dropna())  # Compute the average speed for the session
        avg_speeds.append(avg_speed)

    # ✅ Generate Scatter Plot
    plt.figure(figsize=(8, 5))
    plt.scatter(day_numbers, avg_speeds, color='blue', label="Average Speed (mm/sec)")
    plt.plot(day_numbers, avg_speeds, linestyle='--', color='gray', alpha=0.7)

    plt.xlabel("Day Number")
    plt.ylabel("Average Speed (mm/sec)")
    plt.title(f"Eye Movement Speed Trend Over 7 Days - {participant_name}")
    plt.xticks(day_numbers)
    plt.legend()
    plt.grid(True)

    # ✅ Save & Show Graph
    graph_path = f"{folder_path}/{participant_name}_weekly_speed_trend.png"
    plt.savefig(graph_path)
    plt.show()

    print(f"Weekly speed trend graph saved to: {graph_path}")

# Placeholder for function call
print("Function ready to visualize weekly speed trends.")    

if __name__ == "__main__":
    while True:
        patient_name = input("Enter patient name (or type 'list' to see existing folders): ").strip()

        if patient_name.lower() == "list":
            existing_patients = os.listdir("deterministic_model_test")
            if existing_patients:
                print("Existing patient records:", ", ".join(existing_patients))
            else:
                print("No existing patient records found.")
            continue

        if patient_name:
            patient_folder = f"deterministic_model_test/{patient_name}"
            if os.path.exists(patient_folder):
                print(f"Continuing tracking for existing patient: {patient_name}")
            else:
                print(f"Creating new tracking folder for patient: {patient_name}")
            break
        else:
            print("Error: Patient name cannot be empty.")

    track_eye_speed(patient_name, tracking_duration=10)
