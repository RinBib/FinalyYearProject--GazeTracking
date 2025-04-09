# pyright: reportMissingImports=false
# pyright: reportMissingModuleSource=false
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
from fpdf import FPDF
import shutil
import joblib

from tensorflow.keras.models import load_model


# Load the trained model
cognitive_model = load_model("cognitive_classifier_model.h5")

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
    os.makedirs(folder_path, exist_ok=True)  # Ensure folder exists

    # Get all CSVs for this patient
    existing_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    total_days = len(existing_files)  # How many total days recorded

    week_number = (total_days // 7) + 1  # Week number (every 7 days is a new week)
    day_number = (total_days % 7) + 1     # Day number inside the week (1-7)

    # 👇 Create filename using week and day
    filename = f"{patient_name}_w{week_number}_d{day_number}.csv"

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


# deterministic algorithm
def check_weekly_prediction(patient_name, min_data_points=30, min_fixations=20, min_blinks=10): #min_saccades=5):

    

    folder_path = f"deterministic_model_test/{patient_name}"
    files = sorted([f for f in os.listdir(folder_path) if f.endswith(".csv")])

    if len(files) < 7:
        print(f"Not enough data for {patient_name}. {len(files)}/7 sessions completed.")
        return "Not enough data for deterministic prediction."

    speeds, fixations, blink_frequencies, blink_durations = [], [], [], []
    #saccade_counts, saccade_durations = [], []
    total_data_points, total_fixations, total_blinks, total_saccades = 0, 0, 0, 0

    for file in files[-7:]:
        df = pd.read_csv(os.path.join(folder_path, file))


        # 🛡️ Add this check to avoid crashing!
        required_cols = ['Speed_mm_per_sec', 'Fixation_Detected', 'Blink_Count', 'Blink_Duration']
        if not all(col in df.columns for col in required_cols):
            print(f"[WARNING] Skipping file {file} because missing important columns.")
            continue  # Skip bad file
        
        valid_speeds = df["Speed_mm_per_sec"].dropna().tolist()
        valid_fixations = df["Fixation_Detected"].dropna().sum()
        valid_blink_freqs = df["Blink_Count"].dropna().tolist()
        valid_blink_durations = df["Blink_Duration"].dropna().tolist()
        #valid_saccade_counts = df["Saccade_Count"].dropna().tolist()
        #valid_saccade_durations = df["Saccade_Duration"].dropna().tolist()

        speeds.extend(valid_speeds)
        fixations.append(valid_fixations)
        blink_frequencies.extend(valid_blink_freqs)
        blink_durations.extend(valid_blink_durations)
        #saccade_counts.extend(valid_saccade_counts)
        #saccade_durations.extend(valid_saccade_durations)

        total_data_points += len(valid_speeds)
        total_fixations += valid_fixations
        total_blinks += len(valid_blink_durations)
        #total_saccades += len(valid_saccade_counts)

    # Check if enough data collected
    if total_data_points < min_data_points * 7 or total_fixations < min_fixations * 7 or total_blinks < min_blinks * 7: # or total_saccades #< min_saccades * 7:
        print(f"Not enough data collected for {patient_name}.")
        return "Not enough data for deterministic prediction."

    # Calculate averages
    avg_speed = np.mean(speeds)
    avg_fixations = np.mean(fixations)
    avg_blink_freq = np.mean(blink_frequencies)
    avg_blink_duration = np.mean(blink_durations)
    #avg_saccade_count = np.mean(saccade_counts)
    #avg_saccade_duration = np.mean(saccade_durations)

    # --- Check Each Feature Individually ---
    healthy_features = 0
    total_features = 4

    print("\n===== Feature-by-Feature Health Check =====")

    # Blink Rate (blinks per second)
    if 0.2 <= avg_blink_freq <= 0.5:
        healthy_features += 1
        print("Blink Rate: Healthy ")
    else:
        print("Blink Rate: Abnormal ")

    # Blink Duration (ms)
    if 200 <= avg_blink_duration <= 300:
        healthy_features += 1
        print("Blink Duration: Healthy ")
    else:
        print("Blink Duration: Abnormal ")

    # Speed (mm/sec)
    if 5 <= avg_speed <= 20:
        healthy_features += 1
        print("Speed: Healthy ")
    else:
        print("Speed: Abnormal ")

    # Fixations (number per session)
    if avg_fixations >= 50:
        healthy_features += 1
        print("Fixation Count: Healthy ")
    else:
        print("Fixation Count: Abnormal ")

    # Saccades (number per session)
    #if 5 <= avg_saccade_count <= 20:
        #healthy_features += 1
        #print("Saccade Count: Healthy ")
    #else:
        #print("Saccade Count: Abnormal ")

    # ===== Majority Voting =====
    print(f"\nHealthy Features: {healthy_features}/{total_features}")

    if healthy_features >= 2:
        prediction = "Normal Eye Movement (Healthy)"
    else:
        prediction = "Possible Cognitive Impairment (Check Attention / Fatigue / Neurology)"

    print(f"\nFINAL DETERMINISTIC PREDICTION: {prediction}")
    return prediction





    
def plot_weekly_speed_trend(patient_name):
    folder_path = f"deterministic_model_test/{patient_name}"
    
    # Ensure folder exists
    if not os.path.exists(folder_path):
        print(f"Error: No data found for {patient_name}.")
        return
    
    files = sorted([f for f in os.listdir(folder_path) if f.endswith(".csv")])


    if len(files) < 7:
        print(f"Not enough data for {patient_name}. {len(files)}/7 sessions completed.")
        return

    day_numbers = []
    avg_speeds = []
    avg_fixations = []
    avg_blink_freq = []
    avg_blink_duration = []
    #avg_saccade_count = []
    #avg_saccade_duration = []


    for idx, file in enumerate(files[-7:]):
        df = pd.read_csv(os.path.join(folder_path, file))

        required_cols = ['Speed_mm_per_sec', 'Fixation_Detected', 'Blink_Count', 'Blink_Duration']
        if not all(col in df.columns for col in required_cols):
            print(f"[WARNING] Skipping {file} because it is missing important columns.")
            continue  # Skip this bad file

        avg_speed = np.mean(df["Speed_mm_per_sec"].dropna())
        avg_fixation = df["Fixation_Detected"].dropna().sum()
        avg_blink_f = np.mean(df["Blink_Count"].dropna())
        avg_blink_d = np.mean(df["Blink_Duration"].dropna())
        # optional if you still want to include saccade trends
        #avg_saccade_c = np.mean(df["Saccade_Count"].dropna()) if "Saccade_Count" in df.columns else np.nan
        #avg_saccade_d = np.mean(df["Saccade_Duration"].dropna()) if "Saccade_Duration" in df.columns else np.nan

        avg_speeds.append(avg_speed)
        avg_fixations.append(avg_fixation)
        avg_blink_freq.append(avg_blink_f)
        avg_blink_duration.append(avg_blink_d)
        #avg_saccade_count.append(avg_saccade_c)
        #avg_saccade_duration.append(avg_saccade_d)
        day_numbers.append(idx + 1)
 
        
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
    #plt.show()

    # Fixation Plot
    plt.figure(figsize=(8, 5))
    plt.plot(day_numbers, avg_fixations, marker='s', linestyle='--', color='green', label="Total Fixations")
    plt.xlabel("Day Number")
    plt.ylabel("Fixations Count")
    plt.title(f"Fixation Trend Over 7 Days - {patient_name}")
    #plt.grid(True)
     # Save & Show Graph
    graph_path = f"{folder_path}/{patient_name}_weekly_fixation_trend.png"
    plt.savefig(graph_path)
    plt.legend()
    #plt.show()
    
    
    
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
    
    #plt.show()

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
    
    #plt.show()

#  PLOT SACCADE COUNT TREND (NEW!)
    #plt.figure(figsize=(8, 5))
    #plt.plot(day_numbers, avg_saccade_count, marker='*', linestyle='-', color='orange', label="Saccade Count")
    #plt.xlabel("Day Number")
    #plt.ylabel("Saccades per Session")
    #plt.title(f"Saccade Count Trend Over 7 Days - {patient_name}")
    #plt.legend()
    #plt.grid(True)
    #graph_path = f"{folder_path}/{patient_name}_saccade_count_trend.png"
    #plt.savefig(graph_path)
    
    #plt.show()

    #  PLOT SACCADE DURATION TREND (NEW!)
    #plt.figure(figsize=(8, 5))
    #plt.plot(day_numbers, avg_saccade_duration, marker='h', linestyle='-', color='brown', label="Saccade Duration (ms)")
    #plt.xlabel("Day Number")
    #plt.ylabel("Saccade Duration (ms)")
    #plt.title(f"Saccade Duration Trend Over 7 Days - {patient_name}")
    #plt.legend()
    #plt.grid(True)
    #graph_path = f"{folder_path}/{patient_name}_saccade_duration_trend.png"
    #plt.savefig(graph_path)
    
    #plt.show()




def generate_pdf_report(patient_name, week_number, deterministic_prediction, ai_prediction, folder_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf.cell(200, 10, txt=f"Cognitive Weekly Report - {patient_name}", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"Date and Time: {now}", ln=True)
    pdf.cell(200, 10, txt=f"Week: {week_number}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Deterministic Prediction:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, deterministic_prediction)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="AI Model Prediction:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, ai_prediction)
    pdf.ln(5)

    # Save the file
    report_path = os.path.join(folder_path, f"{patient_name}_weekly_report_Week{week_number}.pdf")
    pdf.output(report_path)

    print(f"[INFO] PDF report saved to: {report_path}")



def generate_monthly_report(patient_name):
    folder_path = f"deterministic_model_test/{patient_name}"
    summary_file = os.path.join(folder_path, "weekly_summary.csv")

    if not os.path.exists(summary_file):
        print("[INFO] No weekly summaries found. Skipping monthly report.")
        return

    df = pd.read_csv(summary_file)

    if len(df) < 4:
        print("[INFO] Not enough weeks (4) completed for monthly report.")
        return

    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Monthly Cognitive Report - {patient_name}", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Date and Time: {now}", ln=True)
    pdf.ln(10)

    # Add each week's prediction
    for idx, row in df.iterrows():
        week = row['Week']
        prediction = row['Prediction']
        pdf.cell(200, 10, txt=f"Week {int(week)}: {prediction}", ln=True)

    pdf.ln(10)

    # Trend analysis
    label_to_score = {
        "Normal Eye Movement": 3,
        "Possible Restlessness / Attention Issues": 2,
        "Possible Fatigue / Drowsiness": 2,
        "Possible Attention Deficit / High Cognitive Load": 1,
        "Possible Neurological Disorder (Check Medical Attention)": 0
    }
    df['Score'] = df['Prediction'].map(label_to_score)

    first_half = df['Score'][:2].mean()
    second_half = df['Score'][2:].mean()

    trend = ""
    if second_half > first_half:
        trend = "Cognitive performance is improving over the month."
    elif second_half < first_half:
        trend = "Cognitive performance is declining over the month."
    else:
        trend = "No clear trend detected."

    pdf.multi_cell(0, 10, f"Trend Analysis: {trend}")

    # Save the PDF
    monthly_report_path = os.path.join(folder_path, f"{patient_name}_Monthly_Report.pdf")
    pdf.output(monthly_report_path)

    print(f"[INFO] Monthly report saved to: {monthly_report_path}")


def save_weekly_summary(patient_name, week_number, prediction):
    folder_path = f"deterministic_model_test/{patient_name}"
    summary_file = os.path.join(folder_path, "weekly_summary.csv")

    # Create the file if it doesn't exist
    if not os.path.exists(summary_file):
        with open(summary_file, mode='w') as file:
            file.write("Week,Prediction\n")

    # Append this week's prediction
    with open(summary_file, mode='a') as file:
        file.write(f"{week_number},{prediction}\n")


def import_existing_data_and_generate_report(patient_name, folder_path):
    

    patient_folder = f"deterministic_model_test/{patient_name}"
    os.makedirs(patient_folder, exist_ok=True)

    # Copy all CSVs
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            src = os.path.join(folder_path, file)
            dst = os.path.join(patient_folder, file)
            if not os.path.exists(dst):
                shutil.copy(src, dst)

    print(f"[INFO] Imported {len(os.listdir(folder_path))} CSV files into {patient_folder}")

    # --- After importing files
    num_csv = len([f for f in os.listdir(patient_folder) if f.endswith(".csv")])
    if num_csv >= 7:
        deterministic_prediction = check_weekly_prediction(patient_name)
        plot_weekly_speed_trend(patient_name)

        # 🧠 Instead of calling run_ai_model_on_week, do it manually:
        all_data = []
        for file in sorted(os.listdir(patient_folder)):
            if file.endswith(".csv"):
                df = pd.read_csv(os.path.join(patient_folder, file))
                required_columns = [
                    'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
                    'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
                    'fixation_duration', 'Blink_Count', 'Blink_Duration']
                    #'Saccade_Count', 'Saccade_Duration'
                
                missing_cols = [col for col in required_columns if col not in df.columns]

                if missing_cols:
                    print(f"[WARNING] Skipping {file} because missing columns: {missing_cols}")
                else:
                    all_data.append(df[required_columns])


        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            # 🛠️ Keep only important features (no saccades)
            selected_features = [
                'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
                'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
                'fixation_duration', 'Blink_Count', 'Blink_Duration'
            ]
            combined_df = combined_df[selected_features]
            #  Load the saved scaler
            scaler = joblib.load('scaler.pkl')
            features = combined_df.values
            features_scaled = scaler.transform(features)
            features_for_prediction = np.expand_dims(features, axis=0)
            prediction = cognitive_model.predict(features_for_prediction)
            predicted_class = np.argmax(prediction, axis=1)[0]
            ai_prediction = "IMPAIRED" if predicted_class == 0 else "HEALTHY"
        else:
            ai_prediction = "Not enough data for AI model"

        # Debug prints
        print("[DEBUG] Deterministic Prediction:", deterministic_prediction)
        print("[DEBUG] AI Prediction:", ai_prediction)
        

        week_number = num_csv // 7

        if deterministic_prediction is not None and ai_prediction is not None:
            generate_pdf_report(patient_name, week_number, deterministic_prediction, ai_prediction, patient_folder)
            save_weekly_summary(patient_name, week_number, deterministic_prediction)
        else:
            print("[WARNING] Predictions incomplete. Skipping PDF generation.")

    # After saving weekly summary, check if 4 weeks done
    if num_csv >= 28:
        generate_monthly_report(patient_name)









if __name__ == "__main__":
    while True:
        print("\nWhat would you like to do?")
        print("1. Run New Test (using webcam)")
        print("2. Import Folder of CSV Files and Generate Report")
        print("3. Exit Program")

        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            #  RUN NEW TEST
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
                if not os.path.exists(patient_folder):
                    print(f"Creating new tracking folder for patient: {patient_name}")
                else:
                    print(f"Continuing tracking for existing patient: {patient_name}")

                track_eye_activity(patient_name, tracking_duration=10)

                #  AFTER 7 CSVs
                if len([f for f in os.listdir(patient_folder) if f.endswith(".csv")]) >= 7:
                    deterministic_prediction = check_weekly_prediction(patient_name)
                    plot_weekly_speed_trend(patient_name)

                    #  AI Prediction
                    all_data = []
                    for file in sorted(os.listdir(patient_folder)):
                        if file.endswith(".csv"):
                            df = pd.read_csv(os.path.join(patient_folder, file))
                            required_columns = [
                                'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
                                'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
                                'fixation_duration', 'Blink_Count', 'Blink_Duration',
                                'Saccade_Count', 'Saccade_Duration'
                            ]
                            if all(col in df.columns for col in required_columns):
                                all_data.append(df[required_columns])

                    if all_data:
                        combined_df = pd.concat(all_data, ignore_index=True)
                        # 🛠️ Select only the 10 important features (no saccades)
                        selected_features = [
                            'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
                            'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
                            'fixation_duration', 'Blink_Count', 'Blink_Duration'
                        ]
                        combined_df = combined_df[selected_features]
                        scaler = joblib.load('scaler.pkl')
                        features = combined_df.values
                        features_scaled = scaler.transform(features)
                        features_for_prediction = np.expand_dims(features, axis=0)
                        prediction = cognitive_model.predict(features_for_prediction)
                        predicted_class = np.argmax(prediction, axis=1)[0]
                        ai_prediction = "IMPAIRED" if predicted_class == 0 else "HEALTHY"
                    else:
                        ai_prediction = "Not enough data for AI model"

                    # 📄 Generate PDF report
                    week_number = len([f for f in os.listdir(patient_folder) if f.endswith(".csv")]) // 7
                    if deterministic_prediction is not None and ai_prediction is not None:
                        generate_pdf_report(patient_name, week_number, deterministic_prediction, ai_prediction, patient_folder)
                        save_weekly_summary(patient_name, week_number, deterministic_prediction)

                    if len([f for f in os.listdir(patient_folder) if f.endswith(".csv")]) >= 28:
                        generate_monthly_report(patient_name)
            else:
                print("Error: Patient name cannot be empty.")

        elif choice == "2":
            # 📂 IMPORT CSV FILES
            folder_to_import = input("Enter path to folder containing CSV files: ").strip()
            target_patient_name = input("Enter target patient name: ").strip()

            import_existing_data_and_generate_report(target_patient_name, folder_to_import)

        elif choice == "3":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select 1, 2, or 3.")



