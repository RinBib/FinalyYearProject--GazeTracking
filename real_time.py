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
import tkinter as tk
from tkinter import filedialog
from tensorflow.keras.models import load_model
# pyright: reportMissingImports=false

# Load the trained cognitive classification model
cognitive_model = load_model("cognitive_classifier_model.h5")

# FUNCTION TO PREDICT USING THE LOADED MODEL
def predict_cognitive_state(features):
    features = np.array(features)  # Make sure it's numpy
    features = np.expand_dims(features, axis=0)  # (1, 12)
    features = np.expand_dims(features, axis=1)  # (1, 1, 12)  --> LSTM expects sequences!
    
    prediction = cognitive_model.predict(features)
    predicted_class = np.argmax(prediction, axis=1)[0]
    return predicted_class







# Ensures python can find gaze_tracking
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



# Initialize GazeTracking
gaze = GazeTracking()
# face detection
face_detector = dlib.get_frontal_face_detector()

FRAME_WIDTH, FRAME_HEIGHT = 640, 480
# (x1,y1) (x2,y2)
SAFE_ZONE = (200, 100, 440, 380) 

SACCADE_VELOCITY_THRESHOLD = 3.0# deg/sec (Adjust this based on research)
SACCADE_DURATION_THRESHOLD = 50  # ms (Average duration of a saccade)
SACCADE_MIN_DURATION = 180  # ✅ Ensure only real saccades are counted

# Constants for real-world conversion
DPI = 96  
SCREEN_DISTANCE_MM = 600 
MAX_DISTANCE_MM = 800  #  Maximum distance before pausing tracking
# Assume a reference face width at 60 cm distance
KNOWN_FACE_WIDTH_MM = 150  # Approximate human face width in mm
FOCAL_LENGTH = 500  # Estimated camera focal length 

PIXEL_TO_MM = 25.4 / DPI  



def open_file_explorer():
    root = tk.Tk()
    root.withdraw()  # Hide the small tkinter window
    file_path = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV Files", "*.csv")]
    )
    return file_path




def predict_from_csv(file_path, patient_name):
    # Load the imported CSV
    df = pd.read_csv(file_path)

    # Make sure the CSV has the needed columns
    required_columns = [
        'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
        'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
        'fixation_duration', 'Blink_Count', 'Blink_Duration',
        'Saccade_Count', 'Saccade_Duration'
    ]

    for col in required_columns:
        if col not in df.columns:
            print(f"Missing column: {col}")
            return

    # Take the last 20 rows (like a sequence)
    if len(df) < 20:
        print("Not enough data (need at least 20 rows for LSTM model).")
        return

    last_20 = df[required_columns].tail(20).values

    # Reshape to (1, 20, 12) for LSTM
    features_for_prediction = np.expand_dims(last_20, axis=0)

    # Predict with AI model
    prediction = cognitive_model.predict(features_for_prediction)
    predicted_class = np.argmax(prediction, axis=1)[0]

    if predicted_class == 0:
        print("[MODEL PREDICTION] Cognitive State: IMPAIRED")
    else:
        print("[MODEL PREDICTION] Cognitive State: HEALTHY")

    # Also apply deterministic prediction
    print("\nRunning deterministic rule-based prediction...")
    folder_path = f"deterministic_model_test/{patient_name}"
    os.makedirs(folder_path, exist_ok=True)  # Just to be sure folder exists
    df.to_csv(f"{folder_path}/{patient_name}_imported_file.csv", index=False)

    # Call your deterministic functions
    check_weekly_prediction(patient_name)
    plot_weekly_speed_trend(patient_name)

 
 
 
def estimate_distance(face_width_px):
    """
    Estimates the user's distance from the screen using face size.
    - Larger faces mean closer distance.
    - Smaller faces mean further distance.
    """
    if face_width_px == 0:
        return SCREEN_DISTANCE_MM  # Default if no face is detected
    return (KNOWN_FACE_WIDTH_MM * FOCAL_LENGTH) / face_width_px
 
 
 
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
    time_diff = max((curr_time - prev_time) / 1000, 0.001)  #  Prevents division by zero


    if time_diff <= 0:
        return 0, 0, 0, time_diff # Avoid division by zero

    # Convert pixels to mm
    distance_mm = distance_px * PIXEL_TO_MM * 2  #  Scaling factor to better match real eye movements

    speed_mm_sec = distance_mm / time_diff

    # Convert mm to degrees of visual angle
    speed_deg_sec = 2 * math.degrees(math.atan(distance_mm / (2 * SCREEN_DISTANCE_MM))) / time_diff
    print(f"Distance in mm: {distance_mm}, Time diff: {time_diff}, Speed in mm/sec: {speed_mm_sec}")

    return distance_px / time_diff, speed_mm_sec, speed_deg_sec, time_diff


def get_next_filename(patient_name):
    folder_path = f"deterministic_model_test/{patient_name}"
    os.makedirs(folder_path, exist_ok=True)  # Create folder if missing

    # Find existing patient files
    existing_files = [f for f in os.listdir(folder_path) if f.startswith(patient_name)]

    # How many total days already recorded
    total_days = len(existing_files)

    # Calculate week number
    week_number = (total_days // 7) + 1  # Every 7 days = next week

    # Calculate day number inside the week
    day_number = (total_days % 7) + 1  # 1 to 7

    # Create filename like: evie1_1.csv
    filename = f"{patient_name}{day_number}_{week_number}.csv"

    return os.path.join(folder_path, filename)





def track_eye_activity(patient_name, tracking_duration=10):
    log_file = get_next_filename(patient_name)
    initialize_csv(log_file, ["Timestamp", "Left_Pupil_X", "Left_Pupil_Y",
                              "Right_Pupil_X", "Right_Pupil_Y", "Speed_px_per_sec",
                              "Speed_mm_per_sec", "Speed_deg_per_sec", "Fixation_Detected",
                              "Fixation_X", "Fixation_Y", "fixation_duration", "Blink_Count",
                              "Blink_Duration", "Saccade_Count", "Saccade_Duration"])

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

    saccade_count = 0  #  Track Total Saccades
    saccade_durations = []  #  Store Saccade Durations
    saccade_start_time = None  #  Track When Saccade Starts
    saccade_detected = False  #  Default State

    # Moving shape properties
    shape_x, shape_y = 320, 240  # Start in center
    shape_radius = 20
    SCREEN_DISTANCE_MM = 600  #  Default distance if no face is detected at the start


    while True:
        ret, frame = webcam.read()
        if not ret:
            break

        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector(gray)
        if faces:
            
            for face in faces:  #  Loop through detected faces
                face_width_px = face.right() - face.left()  #  Get face width in pixels
                SCREEN_DISTANCE_MM = estimate_distance(face_width_px)  # Update distance dynamically
                print(f"[DEBUG] Estimated Distance: {SCREEN_DISTANCE_MM:.2f} mm")
            
                #  Debugging output
                #  CHECK IF USER IS TOO FAR
                if SCREEN_DISTANCE_MM > MAX_DISTANCE_MM:
                    print("[WARNING] Too far from the screen! Pausing tracking...")

                    #  Turn screen red
                    red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8)  # Full red frame
                    frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  # Blend with transparency
        
                    # Show Warning Text
                    cv2.putText(frame, "Too Far! Move Closer", (150, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

                    #  Pause timer if not already paused
                    if last_pause_start is None:
                        last_pause_start = time.time()  #  Set pause start time once
                else:
            #  Resume timer if user moves closer
                    if last_pause_start is not None:
                        paused_time += time.time() - last_pause_start  #  Accumulate paused time
                        last_pause_start = None  #  Reset pause tracker

        else:
            #  If no face detected, treat it like the user is too far
            print("[WARNING] No face detected! Pausing tracking...")

            #  Turn screen red
            red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8)  
            frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  

            #  Show Warning Text
            cv2.putText(frame, "No Face Detected! Please Step Closer", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

            #  Pause timer if not already paused
            if last_pause_start is None:
                last_pause_start = time.time()
            
            #SCREEN_DISTANCE_MM = 600  # Default to 60 cm if face is not detected
        
        # FIX: Initialize fixation text BEFORE checking for faces
        fixation_text = "No Fixation"
        fixation_color = (0, 0, 255)  # Red (No Fixation)
        fixation_duration = 0
        blink_text = "Eyes Open"
        blink_color = (0, 255, 0)
        saccade_text = "No Saccade"
        saccade_color = (255, 255, 255)  # White (No Saccade)
        
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
                
                 #  BLINK DETECTION
                if gaze.pupil_left_coords() is None and gaze.pupil_right_coords() is None:
                    blink_text = "Blink Detected"
                    blink_color = (0, 0, 255)  # Red when blinking

                    if not eyes_closed:
                        blink_count += 1
                        eyes_closed = True
                        blink_start_time = time.time()  #  Store blink start time
                else:
                    if eyes_closed:
                        blink_duration = (time.time() - blink_start_time) * 1000  #  Calculate blink duration in ms
                        blink_durations.append(blink_duration)
                    eyes_closed = False
                
                

                if pupils_located():
                    left_pupil = gaze.pupil_left_coords()
                    right_pupil = gaze.pupil_right_coords()

                    if left_pupil and right_pupil and None not in left_pupil and None not in right_pupil:
                        timestamp = datetime.now().timestamp() * 1000
                        #  Ensure prev_timestamp is defined
                        if prev_timestamp is not None:
                            time_diff = (timestamp - prev_timestamp) / 1000  # Convert ms to sec
                        else:
                            time_diff = 0  # First frame, no time difference

                        curr_x = (left_pupil[0] + right_pupil[0]) / 2
                        curr_y = (left_pupil[1] + right_pupil[1]) / 2

                        speed_px_sec, speed_mm_sec, speed_deg_sec = 0, 0, 0  
                        # SPEED CALCULATION
                        if prev_x is not None and prev_y is not None:
                            speed_px_sec, speed_mm_sec, speed_deg_sec, time_diff = calculate_speed(
                                (prev_x, prev_y), (curr_x, curr_y), prev_timestamp, timestamp
                            )
                            
                            #  Print Debugging Info for Speed
                            print(f"[DEBUG] Speed: {speed_deg_sec:.2f} deg/sec | Threshold: {SACCADE_VELOCITY_THRESHOLD} deg/sec")

                            #  Saccade Detection Based on Speed & Duration
                            if speed_deg_sec > SACCADE_VELOCITY_THRESHOLD and time_diff > (SACCADE_MIN_DURATION / 1000):
                                print("[DEBUG] Saccade Detected!")  #  Print confirmation for debugging

                             #  DETECT SACCADE IF SPEED > THRESHOLD
                           # if speed_deg_sec > 30:  # Adjust threshold if needed
                                if not saccade_detected:
                                    saccade_detected = True
                                    saccade_start_time = time.time()
                                    saccade_count += 1  #  INCREMENT SACCADE COUNT
                                    saccade_text = "Saccade Detected"
                                    saccade_color = (255, 0, 0)  # Blue (Saccade Detected)
                            else:
                                if saccade_detected:
                                    saccade_duration = (time.time() - saccade_start_time) * 1000
                                    saccade_durations.append(saccade_duration)
                                    saccade_detected = False  # RESET SACCADE STATE


                            
                            
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
                        avg_saccade_duration = np.mean(saccade_durations) if saccade_durations else 0  
                        
                        # csv
                        log_data(log_file, [
                            datetime.now(), *left_pupil, *right_pupil,
                            speed_px_sec, speed_mm_sec, speed_deg_sec, fixation_detected, fixation_pos[0] if fixation_detected else None,
                            fixation_pos[1] if fixation_detected else None, fixation_duration, blink_count, avg_blink_duration, saccade_count, avg_saccade_duration
                        ])



                        # Update previous position
                        prev_x, prev_y = curr_x, curr_y
                        prev_timestamp = timestamp
                        

                        # ai model

                        features_for_prediction = np.array([
                            left_pupil[0], left_pupil[1], right_pupil[0], right_pupil[1],
                            speed_px_sec, speed_mm_sec, speed_deg_sec,
                            fixation_duration, blink_count, avg_blink_duration,
                            saccade_count, avg_saccade_duration
                        ], dtype=np.float32)

                        features_for_prediction = features_for_prediction.reshape(1, 20, len(features_for_prediction) // 20)

                        prediction = cognitive_model.predict(features_for_prediction)
                        predicted_class = np.argmax(prediction, axis=1)[0]

                        if predicted_class == 0:
                            print("[MODEL PREDICTION] Cognitive State: IMPAIRED")
                        else:
                            print("[MODEL PREDICTION] Cognitive State: HEALTHY")




                        
                        
                        
                    else:
                        # If pupils are None, also pause the timer
                        if last_pause_start is None:
                            last_pause_start = time.time()
                            print("[DEBUG] Pausing timer - Eye tracking lost.")

                cv2.putText(frame, fixation_text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, fixation_color, 2)
                cv2.putText(frame, blink_text, (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)
                cv2.putText(frame, saccade_text, (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, saccade_color, 2)

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
        
        #  Display estimated distance in bottom-left corner of UI
        distance_text = f"Distance: {SCREEN_DISTANCE_MM:.1f} mm"
        cv2.putText(frame, distance_text, (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        #  Adjust timer logic based on distance
        if SCREEN_DISTANCE_MM > MAX_DISTANCE_MM or last_pause_start is not None:
            #  Keep pausing the timer if user is too far
            remaining_time = max(0, tracking_duration - (time.time() - start_time - paused_time - (time.time() - last_pause_start)))
        else:
            #  Resume normal timer if user moves closer
            remaining_time = max(0, tracking_duration - (time.time() - start_time - paused_time))

        cv2.imshow("Eye Speed, Fixation, Blinking and Tracking", frame)


        # Stop when time is up
        if remaining_time <= 0:
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()
    print(f"Speed test completed. Data saved to {log_file}")



def check_weekly_prediction(patient_name, min_data_points=100, min_fixations=50, min_blinks=20, min_saccades=10):
    folder_path = f"deterministic_model_test/{patient_name}"
    files = sorted([f for f in os.listdir(folder_path) if f.startswith(f"{patient_name}_speed_test") and f.endswith(".csv")])

    if len(files) < 7:
        print(f"Not enough data for {patient_name}. {len(files)}/7 sessions completed.")
        return

    speeds, fixations, blink_frequencies, blink_durations = [], [], [], []
    saccade_counts, saccade_durations = [], []
    total_data_points, total_fixations, total_blinks, total_saccades = 0,0,0,0

    for file in files[-7:]:  
        df = pd.read_csv(os.path.join(folder_path, file))
        valid_speeds = df["Speed_mm_per_sec"].dropna().tolist()
        
        # FIXATION
        valid_fixations = df["Fixation_Detected"].dropna().sum() 
        valid_blink_freqs = df["Blink_Count"].dropna().tolist()  # Blink frequency per second
        valid_blink_durations = df["Blink_Duration"].dropna().tolist()  # 
        valid_saccade_counts = df["Saccade_Count"].dropna().tolist()
        valid_saccade_durations = df["Saccade_Duration"].dropna().tolist()
        
        speeds.extend(valid_speeds)
        fixations.append(valid_fixations)
        blink_frequencies.extend(valid_blink_freqs)
        blink_durations.extend(valid_blink_durations)
        saccade_counts.extend(valid_saccade_counts)
        saccade_durations.extend(valid_saccade_durations)
        
        total_data_points += len(valid_speeds)
        total_fixations += valid_fixations
        total_blinks += len(valid_blink_durations)
        total_saccades += len(valid_saccade_counts)
        
    # Check if there are enough data points
    if total_data_points < min_data_points * 7 or total_fixations < min_fixations * 7 or total_blinks < min_blinks * 7 or total_saccades < min_saccades * 7:
        print(f"Not enough data for {patient_name}. Only {total_data_points}/{min_data_points * 7}, {total_fixations}/{min_fixations * 7} fixations, {total_blinks}/{min_blinks * 7} blinks, {total_saccades}/{min_saccades * 7} saccades collected.")
        return

    avg_speed = np.mean(speeds)
    avg_fixations = np.mean(fixations)
    avg_blink_freq = np.mean(blink_frequencies)
    avg_blink_duration = np.mean(blink_durations)
    avg_saccade_count = np.mean(saccade_counts)
    avg_saccade_duration = np.mean(saccade_durations)
    
    if avg_speed < 5 and avg_fixations < 50 and avg_blink_freq < 0.2 and avg_blink_duration > 400 and avg_saccade_count < 5:
        prediction = "Possible Fatigue / Drowsiness"
    elif 5 <= avg_speed <= 20 and avg_fixations >= 50 and 0.2 <= avg_blink_freq <= 0.5 and 200 <= avg_blink_duration <= 300 and 5 <= avg_saccade_count <= 20:
        prediction = "Normal Eye Movement"
    elif avg_speed > 20 or avg_fixations > 100 or avg_blink_freq > 0.5 and avg_blink_duration < 200 or avg_saccade_count > 20:
        prediction = "Possible Attention Deficit / High Cognitive Load"
    elif avg_blink_duration > 500 or avg_saccade_count < 3:
        prediction = "Possible Neurological Disorder (Check Medical Attention)"
    else:
        prediction = "Possible Restlessness / Attention Issues"
    print(f"Prediction for {patient_name} after 7 days: {prediction}")
    
    
    week_number = len([f for f in os.listdir(folder_path) if f.startswith(f"{patient_name}_speed_test")]) // 7
    save_weekly_summary(patient_name, week_number, prediction)

    # Now check if 4 weekly summaries exist (i.e., 4 weeks = 1 month)
    summary_file = f"deterministic_model_test/{patient_name}/{patient_name}_weekly_summary.csv"
    if os.path.exists(summary_file) and len(pd.read_csv(summary_file)) >= 4:
        plot_monthly_cognitive_trend(patient_name)




# 1 month summary
def save_weekly_summary(patient_name, week_number, prediction):
    folder_path = f"deterministic_model_test/{patient_name}"
    summary_file = os.path.join(folder_path, "weekly_summary.csv")

    # Create the CSV if it doesn't exist yet
    if not os.path.exists(summary_file):
        with open(summary_file, mode='w') as file:
            file.write("Week,Prediction\n")

    with open(summary_file, mode='a') as file:
        file.write(f"{week_number},{prediction}\n")

    
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
    avg_speeds, avg_fixations, avg_blink_freq, avg_blink_duration, avg_saccade_count, avg_saccade_duration = [], [], [], [], [], []

    for file in files[-7:]:  # Get the last 7 files
        df = pd.read_csv(os.path.join(folder_path, file))
        #  Compute the correct values
        avg_speed = np.mean(df["Speed_mm_per_sec"].dropna())  # Average speed
        avg_fixation = df["Fixation_Detected"].dropna().sum()  # Total fixations in session
        avg_blink_f = np.mean(df["Blink_Count"].dropna())  # Average blink frequency
        avg_blink_d = np.mean(df["Blink_Duration"].dropna())  # Average blink duration
        avg_saccade_c = np.mean(df["Saccade_Count"].dropna())  # Average saccade count
        avg_saccade_d = np.mean(df["Saccade_Duration"].dropna())  # Average saccade duration

        #  Append the values to the lists
        avg_speeds.append(avg_speed)
        avg_fixations.append(avg_fixation)  
        avg_blink_freq.append(avg_blink_f)    
        avg_blink_duration.append(avg_blink_d)    
        avg_saccade_count.append(avg_saccade_c)  
        avg_saccade_duration.append(avg_saccade_d)  
        
    # Generate speed Plot
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
    plt.savefig(graph_path)
    plt.legend()
    plt.show()
    
    
    
    #  BLINK FREQUENCY TREND PLOT
    plt.figure(figsize=(8, 5))
    plt.plot(day_numbers, avg_blink_freq, marker='^', linestyle='-', color='purple', label="Blink Frequency (blinks/sec)")
    plt.xlabel("Day Number")
    plt.ylabel("Blink Frequency (blinks/sec)")
    plt.title(f"Blink Frequency Trend Over 7 Days - {patient_name}")
    plt.xticks(day_numbers)
    plt.legend()
    plt.grid(True)
    graph_path = f"{folder_path}/{patient_name}_blinking_frequency_trend.png"
    plt.savefig(graph_path)
    
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
    graph_path = f"{folder_path}/{patient_name}_blink_duration_trend.png"
    plt.savefig(graph_path)
    
    plt.show()

#  PLOT SACCADE COUNT TREND (NEW!)
    plt.figure(figsize=(8, 5))
    plt.plot(day_numbers, avg_saccade_count, marker='*', linestyle='-', color='orange', label="Saccade Count")
    plt.xlabel("Day Number")
    plt.ylabel("Saccades per Session")
    plt.title(f"Saccade Count Trend Over 7 Days - {patient_name}")
    plt.legend()
    plt.grid(True)
    graph_path = f"{folder_path}/{patient_name}_saccade_count_trend.png"
    plt.savefig(graph_path)
    
    plt.show()

    #  PLOT SACCADE DURATION TREND (NEW!)
    plt.figure(figsize=(8, 5))
    plt.plot(day_numbers, avg_saccade_duration, marker='h', linestyle='-', color='brown', label="Saccade Duration (ms)")
    plt.xlabel("Day Number")
    plt.ylabel("Saccade Duration (ms)")
    plt.title(f"Saccade Duration Trend Over 7 Days - {patient_name}")
    plt.legend()
    plt.grid(True)
    graph_path = f"{folder_path}/{patient_name}_saccade_duration_trend.png"
    plt.savefig(graph_path)
    
    plt.show()


def plot_monthly_cognitive_trend(patient_name):
    folder_path = f"deterministic_model_test/{patient_name}"
    summary_file = os.path.join(folder_path, "weekly_summary.csv")

    if not os.path.exists(summary_file):
        print(f"No weekly summary found for {patient_name}.")
        return

    df = pd.read_csv(summary_file)

    if len(df) < 4:
        print(f"Not enough weeks completed. {len(df)}/4 weeks available.")
        return

    plt.figure(figsize=(8, 5))
    plt.plot(df['Week'], df['Prediction'], marker='o', linestyle='--', color='blue')
    plt.title(f"Monthly Cognitive Trend for {patient_name}")
    plt.xlabel("Week Number")
    plt.ylabel("Cognitive State")
    plt.grid(True)

    graph_path = os.path.join(folder_path, f"{patient_name}_monthly_cognitive_trend.png")
    plt.savefig(graph_path)
    plt.show()

    print(f"Monthly trend graph saved to: {graph_path}")

    # predicitons
    label_to_score = {
        "Normal Eye Movement": 3,
        "Possible Restlessness / Attention Issues": 2,
        "Possible Fatigue / Drowsiness": 2,
        "Possible Attention Deficit / High Cognitive Load": 1,
        "Possible Neurological Disorder (Check Medical Attention)": 0
    }

    # Map text labels to numeric scores
    df['Score'] = df['Prediction'].map(label_to_score)

    if df['Score'].isnull().any():
        print("Warning: Some predictions could not be scored.")
    else:
        # Compare first half vs second half
        first_half_avg = df['Score'][:2].mean()
        second_half_avg = df['Score'][2:].mean()

        if second_half_avg > first_half_avg:
            print("Trend Analysis: Cognitive performance is improving over the month.")
        elif second_half_avg < first_half_avg:
            print("Trend Analysis: Cognitive performance is declining over the month.")
        else:
            print("Trend Analysis: No clear trend detected.")




if __name__ == "__main__":
   
    while True:
        choice = input("Choose mode: \n1 - Live Tracking \n2 - Import CSV for Prediction\nEnter 1 or 2: ").strip()

        if choice == "1":
            # Live tracking mode
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

            # Ensure at least 7 sessions before making graph
            if len(os.listdir(f"deterministic_model_test/{patient_name}")) >= 7:
                check_weekly_prediction(patient_name)
                plot_weekly_speed_trend(patient_name)

        elif choice == "2":
            # Import CSV mode
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])

            if not file_path:
                print("No file selected. Exiting.")
                exit()

            patient_name = input("Enter the patient name for this file: ").strip()

            # Now call your function
            predict_from_csv(file_path, patient_name)

        else:
            print("Invalid choice. Please enter 1 or 2.")
