import cv2
import numpy as np
import os
import csv
from datetime import datetime
import sys
import time  
import math  
import pandas as pd  
import matplotlib.pyplot as plt  
import dlib
from gaze_tracking import GazeTracking
from gaze_tracking.fixation import FixationDetector

# Ensures python can find gaze_tracking
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



# Initialize GazeTracking
gaze = GazeTracking()
# face detection
face_detector = dlib.get_frontal_face_detector()

FRAME_WIDTH, FRAME_HEIGHT = 640, 480
# (x1,y1) (x2,y2)
SAFE_ZONE = (200, 100, 440, 380) 

# Constants for real-world conversion
DPI = 96  
SCREEN_DISTANCE_MM = 600  
PIXEL_TO_MM = 25.4 / DPI  
 
# Make csv
def initialize_csv(log_file, headers):
    
    with open(log_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

# Log data
def log_data(log_file, data):
    
    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)
        
def is_head_centered(face):
    
    x, y, w, h = face.left(), face.top(), face.width(), face.height()
    x_center, y_center = x + w // 2, y + h // 2

    # Define oval center and axes (adjust as needed)
    oval_center_x, oval_center_y = 320, 240  # Center of screen
    oval_axis_x, oval_axis_y = 160, 180  # Horizontal and vertical radii

    # Equation of an ellipse: ((x-h)/a)^2 + ((y-k)/b)^2 <= 1
    normalized_x = ((x_center - oval_center_x) ** 2) / (oval_axis_x ** 2)
    normalized_y = ((y_center - oval_center_y) ** 2) / (oval_axis_y ** 2)

    return (normalized_x + normalized_y) <= 1  # Returns True if inside the oval


def pupils_located():
    try:
        if gaze.eye_left and gaze.eye_right:
            if gaze.eye_left.pupil and gaze.eye_right.pupil:
                if gaze.eye_left.pupil.x is not None and gaze.eye_right.pupil.x is not None:
                    print(f"[DEBUG] Left Pupil: ({gaze.eye_left.pupil.x}, {gaze.eye_left.pupil.y})")
                    print(f"[DEBUG] Right Pupil: ({gaze.eye_right.pupil.x}, {gaze.eye_right.pupil.y})")
                    return True
                else:
                    print("[WARNING] Pupils became None after moving.")
            else:
                print("[WARNING] Eye object exists, but pupils are missing.")
        else:
            print("[WARNING] Eye objects are None!")
    except Exception as e:
        print(f"[ERROR] Pupil detection failed: {e}")  
    return False





#def pupils_located():
    #try:
        #if gaze.eye_left and gaze.eye_right:
           # int(gaze.eye_left.pupil.x)
          #  int(gaze.eye_left.pupil.y)
          #  int(gaze.eye_right.pupil.x)
         #   int(gaze.eye_right.pupil.y)
       #     return True
  #  except Exception as e:
 #       # Debugging message
#        print(f"DEBUG Pupil detection failed: {e}")  
 #   return False




# Calculate speed
def calculate_speed(prev_point, curr_point, prev_time, curr_time):
    
    distance_px = np.sqrt((curr_point[0] - prev_point[0])**2 + (curr_point[1] - prev_point[1])**2)
    #time_diff = curr_time - prev_time
    time_diff = (curr_time - prev_time) / 1000  # Convert ms to seconds

    if time_diff <= 0:
        return 0, 0, 0  # Avoid division by zero

    # Convert pixels to mm
    distance_mm = distance_px * PIXEL_TO_MM
    speed_mm_sec = distance_mm / time_diff

    # Convert mm to degrees of visual angle
    speed_deg_sec = 2 * math.degrees(math.atan(distance_mm / (2 * SCREEN_DISTANCE_MM))) / time_diff
    print(f"Distance in mm: {distance_mm}, Time diff: {time_diff}, Speed in mm/sec: {speed_mm_sec}")

    return distance_px / time_diff, speed_mm_sec, speed_deg_sec  


def get_next_filename(patient_name):
    folder_path = f"deterministic_model_test/{patient_name}"
    os.makedirs(folder_path, exist_ok=True)  # Ensure folder exists

    existing_files = [f for f in os.listdir(folder_path) if f.startswith(f"{patient_name}_speed_test") and f.endswith(".csv")]
    next_number = len(existing_files) + 1  

    return f"{folder_path}/{patient_name}_speed_test_{next_number}.csv"




def track_eye_activity(patient_name, tracking_duration=10):
    log_file = get_next_filename(patient_name)
    initialize_csv(log_file, ["Timestamp", "Left_Pupil_X", "Left_Pupil_Y",
                              "Right_Pupil_X", "Right_Pupil_Y", "Speed_px_per_sec", "Speed_mm_per_sec", "Speed_deg_per_sec", "Fixation_Detected", "Fixation_X", "Fixation_Y", "fixation_duration", "Blink_Count", "Blink_Duration"])

    webcam = cv2.VideoCapture(0)

    # Allow webcam to adjust
    time.sleep(2)

    if not webcam.isOpened():
        print("Error: Cannot access the webcam.")
        return

    print(f"Running speed test for {patient_name}... Test will stop automatically after {tracking_duration} seconds.")

    prev_x, prev_y, prev_timestamp = None, None, None
    start_time = time.time()
    paused_time = 0  # Total paused time
    last_pause_start = None  # When pause started
    
    fixation_detector = FixationDetector()
    blink_count = 0  #  Track Blink Count
    eyes_closed = False  #  Track Eye Closed State
    blink_start_time = None  #  Track When Blink Starts
    blink_durations = []  #


    # Moving shape properties
    shape_x, shape_y = 320, 240  # Start in center
    shape_radius = 20

    while True:
        ret, frame = webcam.read()
        if not ret:
            break

        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector(gray)
        # FIX: Initialize fixation text BEFORE checking for faces
        fixation_text = "No Fixation"
        fixation_color = (0, 0, 255)  # Red (No Fixation)
        fixation_duration = 0
        blink_text = "Eyes Open"
        blink_color = (0, 255, 0)
        
        # Update moving shape position (continuous motion)
        absolute_time_elapsed = time.time() - start_time  # Independent of pause tracking
        shape_x = int(320 + 150 * np.sin(absolute_time_elapsed * 2))  # Moves left-right
        shape_y = int(240 + 50 * np.cos(absolute_time_elapsed * 2))  # Moves slightly up/down

        # Draw the moving shape (yellow circle)
        cv2.circle(frame, (shape_x, shape_y), shape_radius, (0, 255, 255), -1)

        speed_mm_sec = None  # Default speed to None

        if faces:
            face = faces[0]  # Use the first detected face
            if is_head_centered(face):
                cv2.putText(frame, "Head Position: OK", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Process gaze tracking when head is properly positioned
                gaze.refresh(frame)
                cv2.waitKey(1)
                
                 # ✅ BLINK DETECTION
                if gaze.pupil_left_coords() is None and gaze.pupil_right_coords() is None:
                    blink_text = "Blink Detected"
                    blink_color = (0, 0, 255)  # Red when blinking

                    if not eyes_closed:
                        blink_count += 1
                        eyes_closed = True
                        blink_start_time = time.time()  # ✅ Store blink start time
                else:
                    if eyes_closed:
                        blink_duration = (time.time() - blink_start_time) * 1000  # ✅ Calculate blink duration in ms
                        blink_durations.append(blink_duration)
                    eyes_closed = False
                
                

                if pupils_located():
                    left_pupil = gaze.pupil_left_coords()
                    right_pupil = gaze.pupil_right_coords()

                    if left_pupil and right_pupil and None not in left_pupil and None not in right_pupil:
                        timestamp = datetime.now().timestamp() * 1000
                        curr_x = (left_pupil[0] + right_pupil[0]) / 2
                        curr_y = (left_pupil[1] + right_pupil[1]) / 2

                        speed_px_sec, speed_mm_sec, speed_deg_sec = 0, 0, 0  
                        # SPEED CALCULATION
                        if prev_x is not None and prev_y is not None:
                            speed_px_sec, speed_mm_sec, speed_deg_sec = calculate_speed(
                                (prev_x, prev_y), (curr_x, curr_y), prev_timestamp, timestamp
                            )

                            if speed_mm_sec is not None and speed_mm_sec > 0:
                                # Resume timer if it was paused
                                if last_pause_start is not None:
                                    paused_time += time.time() - last_pause_start
                                    last_pause_start = None  # Reset pause tracker
                                    print("[DEBUG] Resuming timer - Movement detected.")

                                log_data(log_file, [
                                    datetime.now(), *left_pupil, *right_pupil, speed_px_sec, speed_mm_sec, speed_deg_sec
                                ])
                            else:
                                # If no movement, start pause timer if not already started
                                if last_pause_start is None:
                                    last_pause_start = time.time()
                                    print("[DEBUG] Pausing timer - No movement detected.")
                        else:
                            # If pupils not found, pause timer
                            if last_pause_start is None:
                                last_pause_start = time.time()
                                print("[DEBUG] Pausing timer - No pupils detected.")


                        # fixation detection
                        fixation_detected, fixation_pos, fixation_duration = fixation_detector.detect_fixation((curr_x, curr_y))
                        
                        if fixation_detected:
                            fixation_text = f"Fixation Detected ({fixation_duration:.2f}s)"
                            fixation_color = (0, 255, 0)  # Green (Fixation detected)
                            
                            
                        avg_blink_duration = np.mean(blink_durations) if blink_durations else 0  # Calculate avg blink duration   
                        
                        # csv
                        log_data(log_file, [
                            datetime.now(), *left_pupil, *right_pupil,
                            speed_px_sec, speed_mm_sec, speed_deg_sec, fixation_detected, fixation_pos[0] if fixation_detected else None,
                            fixation_pos[1] if fixation_detected else None, fixation_duration, blink_count, avg_blink_duration
                        ])



                        # Update previous position
                        prev_x, prev_y = curr_x, curr_y
                        prev_timestamp = timestamp
                    else:
                        # If pupils are None, also pause the timer
                        if last_pause_start is None:
                            last_pause_start = time.time()
                            print("[DEBUG] Pausing timer - Eye tracking lost.")

                cv2.putText(frame, fixation_text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, fixation_color, 2)
                cv2.putText(frame, blink_text, (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)


                #  **Speed Display on UI**
                if speed_mm_sec is not None and speed_mm_sec > 0:
                    cv2.putText(frame, f"Speed: {speed_mm_sec:.2f} mm/sec", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                else:
                    cv2.putText(frame, "Speed: N/A", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)  # Red if speed is missing

            else:
                # Start pause timer if head is not centered
                if last_pause_start is None:
                    last_pause_start = time.time()

                # TURN SCREEN RED IF HEAD IS OUT OF POSITION
                red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8)  # Full red frame
                frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  # Blend with transparency
                cv2.putText(frame, "Adjust Head Position!", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

        else:
            # No face detected: Pause the timer and turn screen red
            if last_pause_start is None:
                last_pause_start = time.time()

            red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8)  # Full red frame
            frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  # Blend with transparency
            cv2.putText(frame, "No Face Detected!", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

        # Draw original oval safe zone
        cv2.ellipse(frame, (320, 240), (120, 150), 0, 0, 360, (0, 255, 0), 2)

        #  **Fixed Timer Display Update**
        if last_pause_start is not None:
            # Timer is paused, stop updating elapsed_time
            remaining_time = max(0, tracking_duration - (time.time() - start_time - paused_time - (time.time() - last_pause_start)))
        else:
            # Timer is running normally
            remaining_time = max(0, tracking_duration - (time.time() - start_time - paused_time))

        
        # Ensure the timer updates correctly even when paused
        cv2.putText(frame, f"Time Left: {int(remaining_time)} sec", (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.putText(frame, fixation_text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, fixation_color, 2)

        cv2.imshow("Eye Speed, Fixzation and  Tracking", frame)
        
        

        # Stop when time is up
        if remaining_time <= 0:
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()
    print(f"Speed test completed. Data saved to {log_file}")



def check_weekly_prediction(patient_name, min_data_points=100, min_fixations=50, min_blinks=20):
    folder_path = f"deterministic_model_test/{patient_name}"
    files = sorted([f for f in os.listdir(folder_path) if f.startswith(f"{patient_name}_speed_test") and f.endswith(".csv")])

    if len(files) < 7:
        print(f"Not enough data for {patient_name}. {len(files)}/7 sessions completed.")
        return

    speeds, fixations, blink_frequencies, blink_durations = [], [], [], []
    total_data_points, total_fixations, total_blinks = 0,0,0

    for file in files[-7:]:  
        df = pd.read_csv(os.path.join(folder_path, file))
        valid_speeds = df["Speed_mm_per_sec"].dropna().tolist()
        
        # FIXATION
        valid_fixations = df["Fixation_Detected"].dropna().sum() 
        valid_blink_freqs = df["Blink_Count"].dropna().tolist()  # Blink frequency per second
        valid_blink_durations = df["Blink_Duration"].dropna().tolist()  # 
        
        speeds.extend(valid_speeds)
        fixations.append(valid_fixations)
        blink_frequencies.extend(valid_blink_freqs)
        blink_durations.extend(valid_blink_durations)
        
        total_data_points += len(valid_speeds)
        total_fixations += valid_fixations
        total_blinks += len(valid_blink_durations)

    # Check if there are enough data points
    if total_data_points < min_data_points * 7 or total_fixations < min_fixations * 7 or total_blinks < min_blinks * 7:
        print(f"Not enough data for {patient_name}. Only {total_data_points}/{min_data_points * 7}, {total_fixations}/{min_fixations * 7} fixations, {total_blinks}/{min_blinks * 7}  required data points collected.")
        return

    avg_speed = np.mean(speeds)
    avg_fixations = np.mean(fixations)
    avg_blink_freq = np.mean(blink_frequencies)
    avg_blink_duration = np.mean(blink_durations)

    if avg_speed < 5 and avg_fixations < 50 and avg_blink_freq < 0.2 and avg_blink_duration > 400:
        prediction = "Possible Fatigue / Drowsiness"
    elif 5 <= avg_speed <= 20 and avg_fixations >= 50 and 0.2 <= avg_blink_freq <= 0.5 and 200 <= avg_blink_duration <= 300:
        prediction = "Normal Eye Movement"
    elif avg_speed > 20 or avg_fixations > 100 or avg_blink_freq > 0.5 and avg_blink_duration < 200:
        prediction = "Possible Attention Deficit / High Cognitive Load"
    elif avg_blink_duration > 500:
        prediction = "Possible Neurological Disorder (Check Medical Attention)"
    else:
        prediction = "Possible Restlessness / Attention Issues"
    print(f"Prediction for {patient_name} after 7 days: {prediction}")

    
    
def plot_weekly_speed_trend(patient_name):
    folder_path = f"deterministic_model_test/{patient_name}"
    
    # Ensure folder exists
    if not os.path.exists(folder_path):
        print(f"Error: No data found for {patient_name}.")
        return
    
    files = sorted([f for f in os.listdir(folder_path) if f.startswith(f"{patient_name}_speed_test") and f.endswith(".csv")])

    if len(files) < 7:
        print(f"Not enough data for {patient_name}. {len(files)}/7 sessions completed.")
        return

    day_numbers = list(range(1, 8))
    avg_speeds = []

    for file in files[-7:]:  # Get the last 7 files
        df = pd.read_csv(os.path.join(folder_path, file))
        avg_speed = np.mean(df["Speed_mm_per_sec"].dropna())  # Compute the average speed for the session
        avg_fixations = df["Fixation_Detected"].dropna().sum()
        avg_blink_freq = np.mean(df["Blink_Count"].dropna())  
        avg_blink_duration = np.mean(df["Blink_Duration"].dropna())
        
        avg_speeds.append(avg_speed)
        avg_fixations.append(avg_fixations)
        avg_blink_freq.append(avg_blink_freq)
        avg_blink_duration.append(avg_blink_duration)
        
    # Generate Scatter Plot
    plt.figure(figsize=(8, 5))
    plt.scatter(day_numbers, avg_speeds, color='blue', label="Average Speed (mm/sec)")
    plt.plot(day_numbers, avg_speeds, linestyle='--', color='gray', alpha=0.7)

    plt.xlabel("Day Number")
    plt.ylabel("Average Speed (mm/sec)")
    plt.title(f"Eye Movement Speed Trend Over 7 Days - {patient_name}")
    plt.xticks(day_numbers)
    plt.legend()
    plt.grid(True)

    # Save & Show Graph
    graph_path = f"{folder_path}/{patient_name}_weekly_speed_trend.png"
    plt.savefig(graph_path)
    plt.show()

    # Fixation Plot
    plt.figure(figsize=(8, 5))
    plt.plot(day_numbers, avg_fixations, marker='s', linestyle='--', color='green', label="Total Fixations")
    plt.xlabel("Day Number")
    plt.ylabel("Fixations Count")
    plt.title(f"Fixation Trend Over 7 Days - {patient_name}")
    plt.grid(True)
     # Save & Show Graph
    graph_path = f"{folder_path}/{patient_name}_weekly_fixation_trend.png"
    plt.legend()
    plt.show()
    
    print(f"Weekly speed trend graph saved to: {graph_path}")
    
    #  BLINK FREQUENCY TREND PLOT
    plt.figure(figsize=(8, 5))
    plt.plot(day_numbers, avg_blink_freq, marker='^', linestyle='-', color='purple', label="Blink Frequency (blinks/sec)")
    plt.xlabel("Day Number")
    plt.ylabel("Blink Frequency (blinks/sec)")
    plt.title(f"Blink Frequency Trend Over 7 Days - {patient_name}")
    plt.xticks(day_numbers)
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{folder_path}/{patient_name}_blink_frequency_trend.png")
    plt.show()

    #  BLINK DURATION TREND PLOT
    plt.figure(figsize=(8, 5))
    plt.plot(day_numbers, avg_blink_duration,marker='d', linestyle='-', color='red', label="Blink Duration (ms)")
    plt.xlabel("Day Number")
    plt.ylabel("Blink Duration (ms)")
    plt.title(f"Blink Duration Trend Over 7 Days - {patient_name}")
    plt.xticks(day_numbers)
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{folder_path}/{patient_name}_blink_duration_trend.png")
    plt.show()



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

   # Run tracking for the current session
track_eye_activity(patient_name, tracking_duration=10)

# Ensure at least 7 sessions before making grapgh
if len(os.listdir(f"deterministic_model_test/{patient_name}")) >= 7:
    check_weekly_prediction(patient_name)
    plot_weekly_speed_trend(patient_name)



    
