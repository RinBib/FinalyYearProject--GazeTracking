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
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt  
import dlib
from gaze_tracking import GazeTracking
from gaze_tracking.fixation import FixationDetector
from fpdf import FPDF
import shutil
import joblib


# Load the Random Forest model
cognitive_model = joblib.load('logistic_model.joblib') 
scaler = joblib.load('scaler.pkl')  

# Ensures python can find gaze_tracking
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize GazeTracking
gaze = GazeTracking()
# face detection
face_detector = dlib.get_frontal_face_detector()

FRAME_WIDTH, FRAME_HEIGHT = 640, 480
# (x1,y1) (x2,y2)
SAFE_ZONE = (200, 100, 440, 380) 

# deg/sec (Adjust this based on research)
SACCADE_VELOCITY_THRESHOLD = 3.0 
# ms (Average duration of a saccade)
SACCADE_DURATION_THRESHOLD = 50  
# Ensure only real saccades are counted
SACCADE_MIN_DURATION = 180  

# Constants for real-world conversion
DPI = 96  
SCREEN_DISTANCE_MM = 600 
#  Maximum distance before pausing tracking
MAX_DISTANCE_MM = 800  
# Assume a reference face width at 60 cm distance - gpt
KNOWN_FACE_WIDTH_MM = 150 
# Estimated camera focal length 
FOCAL_LENGTH = 500  
# convert pixel to MM
PIXEL_TO_MM = 25.4 / DPI  
 
def estimate_distance(face_width_px):
    if face_width_px == 0:
        # Default if no face is detected
        return SCREEN_DISTANCE_MM  
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

    # Define oval center and axes 
    oval_center_x, oval_center_y = 320, 240  # Center of screen
    oval_axis_x, oval_axis_y = 160, 180  # Horizontal and vertical radii

    # Equation of an ellipse: ((x-h)/a)^2 + ((y-k)/b)^2 <= 1
    normalized_x = ((x_center - oval_center_x) ** 2) / (oval_axis_x ** 2)
    normalized_y = ((y_center - oval_center_y) ** 2) / (oval_axis_y ** 2)
    # Returns True if inside the oval
    return (normalized_x + normalized_y) <= 1  


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


# Calculate speed
def calculate_speed(prev_point, curr_point, prev_time, curr_time):
    
    distance_px = np.sqrt((curr_point[0] - prev_point[0])**2 + (curr_point[1] - prev_point[1])**2)
    #time_diff = curr_time - prev_time
    time_diff = max((curr_time - prev_time) / 1000, 0.001)  
    # Avoid division by zero
    if time_diff <= 0:
        return 0, 0, 0, time_diff 

    # Convert pixels to mm
    # Scaling matches real eye movements
    distance_mm = distance_px * PIXEL_TO_MM * 2  

    speed_mm_sec = distance_mm / time_diff

    # Convert mm to degrees of visual angle
    speed_deg_sec = 2 * math.degrees(math.atan(distance_mm / (2 * SCREEN_DISTANCE_MM))) / time_diff
    print(f"Distance in mm: {distance_mm}, Time diff: {time_diff}, Speed in mm/sec: {speed_mm_sec}")

    return distance_px / time_diff, speed_mm_sec, speed_deg_sec, time_diff


def get_next_filename(patient_name):
    data_folder = f"deterministic_model_test/{patient_name}" 
    # Ensure folder exists
    os.makedirs(data_folder, exist_ok=True) 

    # Get all CSVs for this patient
    existing_csvs = [f for f in os.listdir(data_folder) if f.endswith(".csv")]
    # How many total days recorded
    total_days = len(existing_csvs)  
    # Week number (every 7 days is a new week)
    week_number = (total_days // 7) + 1 
    # Day number inside the week (1-7)
    day_number = (total_days % 7) + 1     

    #  Create filename using week and day
    filename = f"{patient_name}_w{week_number}_d{day_number}.csv"

    return os.path.join(data_folder, filename)



def track_eye_activity(patient_name, tracking_duration=10, frame_callback=None):
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
    # Total paused time
    paused_time = 0  
    # When pause started
    last_pause_start = None  
    
    fixation_detector = FixationDetector()
    #  Track Blink Count
    blink_count = 0 
    #  Track Eye Closed State
    eyes_closed = False 
    #  Track When Blink Starts
    blink_start_time = None  
    blink_durations = [] 
     
    #  Track Total Saccades
    saccade_count = 0 
    #  Store Saccade Durations
    saccade_durations = []  
    #  Track When Saccade Starts
    saccade_start_time = None 
    #  Default State
    saccade_detected = False  

    # Moving shape properties
    # Start in center
    shape_x, shape_y = 320, 240  
    shape_radius = 20
    #  Default distance if no face is detected at the start
    SCREEN_DISTANCE_MM = 600  


    while True:
        ret, frame = webcam.read()
        if not ret:
            break
        
        if frame_callback:
            frame_callback(frame.copy())

        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector(gray)
        if faces:
             #  Loop through detected faces
            for face in faces: 
                #  Get face width in pixels
                face_width_px = face.right() - face.left()
                # Update distance dynamically
                SCREEN_DISTANCE_MM = estimate_distance(face_width_px)  
                print(f"[DEBUG] Estimated Distance: {SCREEN_DISTANCE_MM:.2f} mm")
            
                #  Debugging output
                #  check if user is too far
                if SCREEN_DISTANCE_MM > MAX_DISTANCE_MM:
                    print("[WARNING] Too far from the screen! Pausing tracking...")

                    # tunr screen red if too far
                    # Full red frame
                    red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8) 
                    # Blend with transparency
                    frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  
        
                    # Warning to user
                    cv2.putText(frame, "Too Far! Move Closer", (150, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

                    # Pause timer if not already paused
                    if last_pause_start is None:
                        # Set pause start time once
                        last_pause_start = time.time()  
                else:
                    #  Resume timer if user moves closer
                    if last_pause_start is not None:
                        # Accumulate paused time
                        paused_time += time.time() - last_pause_start
                        #  Reset pause tracker
                        last_pause_start = None 

        else:
            #  If no face detected...
            print("[WARNING] No face detected! Pausing tracking...")

            # Turn screen red
            red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8)  
            frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  

            # Show Warning Text
            cv2.putText(frame, "No Face Detected! Please Step Closer", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

            #  Pause timer if not already paused
            if last_pause_start is None:
                last_pause_start = time.time()
            
            
        
        # Initialize fixation text BEFORE checking for faces
        fixation_text = "No Fixation"
        # Red (No Fixation)
        fixation_color = (0, 0, 255)  
        fixation_duration = 0
        blink_text = "Eyes Open"
        blink_color = (0, 255, 0)
        saccade_text = "No Saccade"
        # White (No Saccade)
        saccade_color = (255, 255, 255)  
        
        # Update moving shape position 
        # Independent of pause tracking
        absolute_time_elapsed = time.time() - start_time
        # Moves left-right  
        shape_x = int(320 + 150 * np.sin(absolute_time_elapsed * 2))
        # Moves slightly up/down
        shape_y = int(240 + 50 * np.cos(absolute_time_elapsed * 2)) 

        # Draw the moving shape - yellow circle
        cv2.circle(frame, (shape_x, shape_y), shape_radius, (0, 255, 255), -1)
        # Default speed to None
        speed_mm_sec = None  

        if faces:
            # Use the first detected face
            face = faces[0]  
            if is_head_centered(face):
                cv2.putText(frame, "Head Position: OK", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # gaze tracking occurs
                gaze.refresh(frame)
                cv2.waitKey(1)
                
                 # blinking
                if gaze.pupil_left_coords() is None and gaze.pupil_right_coords() is None:
                    blink_text = "Blink Detected"
                    # Red when blinking
                    blink_color = (0, 0, 255)  

                    if not eyes_closed:
                        blink_count += 1
                        eyes_closed = True
                        # Store blink start time
                        blink_start_time = time.time()  
                else:
                    if eyes_closed:
                        # Calculate blink duration in ms
                        blink_duration = (time.time() - blink_start_time) * 1000  
                        blink_durations.append(blink_duration)
                    eyes_closed = False
                
                if pupils_located():
                    left_pupil = gaze.pupil_left_coords()
                    right_pupil = gaze.pupil_right_coords()

                    if left_pupil and right_pupil and None not in left_pupil and None not in right_pupil:
                        timestamp = datetime.now().timestamp() * 1000
                        #  Ensure prev_timestamp is defined
                        if prev_timestamp is not None:
                            # Convert ms to sec
                            time_diff = (timestamp - prev_timestamp) / 1000  
                        else:
                            # First frame, no time difference
                            time_diff = 0  

                        curr_x = (left_pupil[0] + right_pupil[0]) / 2
                        curr_y = (left_pupil[1] + right_pupil[1]) / 2

                        speed_px_sec, speed_mm_sec, speed_deg_sec = 0, 0, 0
                          
                        # calulate speed
                        if prev_x is not None and prev_y is not None:
                            speed_px_sec, speed_mm_sec, speed_deg_sec, time_diff = calculate_speed(
                                (prev_x, prev_y), (curr_x, curr_y), prev_timestamp, timestamp
                            )
                            
                            # Prining in terminal if needs debugguing
                            print(f"[DEBUG] Speed: {speed_deg_sec:.2f} deg/sec | Threshold: {SACCADE_VELOCITY_THRESHOLD} deg/sec")

                            # saccades detecting
                            if speed_deg_sec > SACCADE_VELOCITY_THRESHOLD and time_diff > (SACCADE_MIN_DURATION / 1000):
                                # Print debug
                                print("[DEBUG] Saccade Detected!")  

                                # Detect saccade if speed>saccade
                                # if speed_deg_sec > 30:  
                                if not saccade_detected:
                                    saccade_detected = True
                                    saccade_start_time = time.time()
                                    # Increment saccades
                                    saccade_count += 1  
                                    saccade_text = "Saccade Detected"
                                    # Blue (Saccade Detected)
                                    saccade_color = (255, 0, 0)  
                            else:
                                if saccade_detected:
                                    saccade_duration = (time.time() - saccade_start_time) * 1000
                                    saccade_durations.append(saccade_duration)
                                    saccade_detected = False  


                            if speed_mm_sec is not None and speed_mm_sec > 0:
                                # Resume timer if it was paused
                                if last_pause_start is not None:
                                    paused_time += time.time() - last_pause_start
                                    # Reset pause tracker 
                                    last_pause_start = None  
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
                            # Green (Fixation detected)
                            fixation_color = (0, 255, 0)  
                            
                        # Calculate avg blink duration      
                        avg_blink_duration = np.mean(blink_durations) if blink_durations else 0   
                        avg_saccade_duration = np.mean(saccade_durations) if saccade_durations else 0  
                        
                        # csv log
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

                # speed shows on UI
                if speed_mm_sec is not None and speed_mm_sec > 0:
                    cv2.putText(frame, f"Speed: {speed_mm_sec:.2f} mm/sec", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                else:
                    cv2.putText(frame, "Speed: N/A", (50, 100),
                                # Red if speed is missing
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)  

            else:
                # Start pause timer if head is not centered
                if last_pause_start is None:
                    last_pause_start = time.time()

                # screen is red if head not in oval
                # Full red frame
                red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8) 
                # Blend with transparency
                frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  
                cv2.putText(frame, "Adjust Head Position!", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

        else:
            # No face detected: Pause the timer and turn screen red
            if last_pause_start is None:
                last_pause_start = time.time()
            # Full red frame
            red_overlay = np.full_like(frame, (0, 0, 255), dtype=np.uint8)
            # Blend with transparency
            frame = cv2.addWeighted(frame, 0.3, red_overlay, 0.7, 0)  
            cv2.putText(frame, "No Face Detected!", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

        # Draw original oval safe zone
        cv2.ellipse(frame, (320, 240), (120, 150), 0, 0, 360, (0, 255, 0), 2)

        # timer display
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

        if frame_callback:
            
            frame_callback(frame.copy())
        else:
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
def check_weekly_prediction(patient_name, data_folder, min_data_points=30, min_fixations=20, min_blinks=10): 

    csvs = sorted(
        f for f in os.listdir(data_folder)
        if f.lower().endswith(".csv")
        and not f.lower().startswith("weekly_summary")
    )

    if len(csvs) < 7:
        return "Not enough data for deterministic prediction."

    speeds, fixations, blink_frequencies, blink_durations = [], [], [], []
    
    #saccade_counts, saccade_durations = [], []
    total_data_points, total_fixations, total_blinks, total_saccades = 0, 0, 0, 0

    for file in csvs[-7:]:
        df = pd.read_csv(os.path.join(data_folder, file))


        # Add check of logs to avoid crash
        required_cols = ['Speed_mm_per_sec', 'Fixation_Detected', 'Blink_Count', 'Blink_Duration']
        if not all(col in df.columns for col in required_cols):
            print(f"[WARNING] Skipping file {file} because missing important columns.")
            # Skip bad file
            continue  
        
        valid_speeds = df["Speed_mm_per_sec"].dropna().tolist()
        valid_fixations = df["Fixation_Detected"].dropna().sum()
        valid_blink_freqs = df["Blink_Count"].dropna().tolist()
        valid_blink_durations = df["Blink_Duration"].dropna().tolist()
        # saccades hashed out as not used in prediction, only logged
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
    # # or total_saccades #< min_saccades * 7:
    if total_data_points < min_data_points * 7 or total_fixations < min_fixations * 7 or total_blinks < min_blinks * 7: 
        print(f"Not enough data collected for {patient_name}.")
        return "Not enough data for deterministic prediction."

    # Calculate averages
    avg_speed = np.mean(speeds)
    avg_fixations = np.mean(fixations)
    avg_blink_freq = np.mean(blink_frequencies)
    avg_blink_duration = np.mean(blink_durations)
    #avg_saccade_count = np.mean(saccade_counts)
    #avg_saccade_duration = np.mean(saccade_durations)

    # check feature
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

    # Majority Voting 
    print(f"\nHealthy Features: {healthy_features}/{total_features}")

    if healthy_features >= 2:
        prediction = "Normal Eye Movement (Healthy)"
    else:
        prediction = "Possible Cognitive Impairment (Check Attention / Fatigue / Neurology)"

    print(f"\nFINAL DETERMINISTIC PREDICTION: {prediction}")
    return prediction


def plot_weekly_speed_trend(patient_name, data_folder, week_number):
     
    csvs = sorted(
        f for f in os.listdir(data_folder)
        if f.lower().endswith(".csv")
        and not f.lower().startswith("weekly_summary")
        and not f.lower().startswith("monthly_report")
    )

    if len(csvs) < 7:
        print(f"Not enough data: {len(csvs)}/7 CSVs.")
        return

    
    day_nums, avg_speeds, avg_fixations, avg_blinks, avg_blink_durs = [], [], [], [], []
    for idx, fn in enumerate(csvs[-7:], start=1):
        df = pd.read_csv(os.path.join(data_folder, fn))
        # check
        day_nums.append(idx)
        avg_speeds.append(df["Speed_mm_per_sec"].mean())
        avg_fixations.append(df["Fixation_Detected"].sum())
        avg_blinks.append(df["Blink_Count"].mean())
        avg_blink_durs.append(df["Blink_Duration"].mean())

    
    def _save(x, y, ylabel, title, suffix, marker=None):
        plt.figure(figsize=(8,5))
        if marker:
            plt.plot(x, y, marker=marker, linestyle='-')
        else:
            plt.scatter(x, y)
            plt.plot(x, y, linestyle='--', alpha=0.7)
        plt.title(f"{title} – week {week_number} – {patient_name}")
        plt.xlabel("Day Number")
        plt.ylabel(ylabel)
        plt.xticks(day_nums)
        plt.grid(True)
        fname = f"{patient_name}_week{week_number}_{suffix}.png"
        plt.savefig(os.path.join(data_folder, fname))
        plt.close()

    
    _save(day_nums, avg_speeds,     "Speed (mm/sec)",           "Weekly Speed Trend",    "speed_trend")
    _save(day_nums, avg_fixations,  "Fixation count",           "Weekly Fixation Trend", "fixation_trend",  marker='s')
    _save(day_nums, avg_blinks,     "Blink freq (blinks/sec)",  "Weekly Blink Freq",     "blink_freq",      marker='^')
    _save(day_nums, avg_blink_durs, "Blink duration (ms)",      "Weekly Blink Dur",      "blink_dur",       marker='d')

    print(f"[INFO] Saved week {week_number} graphs into {data_folder}")


def generate_pdf_report(patient_name, week_number, deterministic_prediction, ai_prediction, data_folder):
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

    # Save the file in path
    report_path = os.path.join(data_folder, f"{patient_name}_weekly_report_Week{week_number}.pdf")
    pdf.output(report_path)

    print(f"[INFO] PDF report saved to: {report_path}")


def generate_monthly_report(patient_name, data_folder):
    
    summary_file = os.path.join(data_folder, "weekly_summary.csv")
    if not os.path.exists(summary_file):
        print("[INFO] No weekly summaries found. Skipping monthly report.")
        return

    df = pd.read_csv(summary_file)
    if len(df) < 4:
        print("[INFO] Not enough weeks (<4) in summary; skipping monthly report.")
        return

    # Setup PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Use a plain hyphen here
    pdf.cell(200, 10, txt=f"Monthly Cognitive Report - {patient_name}", ln=True, align="C")
    pdf.ln(10)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(200, 10, txt=f"Date and Time: {now}", ln=True)
    pdf.ln(10)

    # Write each week's entry
    for _, row in df.iterrows():
        week = int(row["Week"])
        pred = row["Prediction"]
        pdf.cell(200, 10, txt=f"Week {week}: {pred}", ln=True)
    pdf.ln(10)

    # Map predictions to numeric scores
    label_to_score = {
        "Normal Eye Movement (Healthy)": 3,
        "Possible Restlessness / Attention Issues": 2,
        "Possible Fatigue / Drowsiness": 2,
        "Possible Attention Deficit / High Cognitive Load": 1,
        "Possible Neurological Disorder (Check Medical Attention)": 0
    }
    
    df["Score"] = df["Prediction"].map(label_to_score)

    first_half = df["Score"].iloc[:2].mean()
    second_half = df["Score"].iloc[2:].mean()

    if second_half > first_half:
        trend = "Cognitive performance is improving over the month."
    elif second_half < first_half:
        trend = "Cognitive performance is declining over the month."
    else:
        trend = "No clear trend detected."

    pdf.multi_cell(0, 10, f"Trend Analysis: {trend}")

    # Save
    monthly_report_path = os.path.join(data_folder, f"{patient_name}_Monthly_Report.pdf")
    pdf.output(monthly_report_path)
    print(f"[INFO] Monthly report saved to: {monthly_report_path}")




def save_weekly_summary(patient_name, week_number, prediction):
    data_folder = f"deterministic_model_test/{patient_name}"
    summary_file = os.path.join(data_folder, "weekly_summary.csv")

    # Create the file if it doesn't exist
    if not os.path.exists(summary_file):
        with open(summary_file, mode='w') as file:
            file.write("Week,Prediction\n")

    # Append this week's prediction
    with open(summary_file, mode='a') as file:
        file.write(f"{week_number},{prediction}\n")


def import_existing_data_and_generate_report(patient_name, session_folder):
    
    
    csvs = sorted(f for f in os.listdir(session_folder) if f.lower().endswith(".csv"))
    num_csv = len(csvs)
    print(f"[INFO] Found {num_csv} CSV(s) in session {session_folder}")

    # Only proceed once we have a full week
    if num_csv < 7:
        print(f"[INFO] Only {num_csv} CSV(s) in {session_folder}, skipping report.")
        return

    # compute week number
    week_number = num_csv // 7

    
    det_pred = check_weekly_prediction(
        patient_name,
        data_folder=session_folder
    )

    
    plot_weekly_speed_trend(
        patient_name,
        data_folder=session_folder,
        week_number=week_number
    )

    
    all_data = []
    for fn in csvs:
        df = pd.read_csv(os.path.join(session_folder, fn))
        required = [
            'Left_Pupil_X','Left_Pupil_Y','Right_Pupil_X','Right_Pupil_Y',
            'Speed_px_per_sec','Speed_mm_per_sec','Speed_deg_per_sec',
            'fixation_duration','Blink_Count','Blink_Duration'
        ]
        if all(c in df.columns for c in required):
            all_data.append(df[required])
        else:
            print(f"[WARNING] Skipping {fn}, missing columns")

    ai_pred = "Inconclusive"
    if all_data:
        combined = pd.concat(all_data, ignore_index=True).dropna()
        if not combined.empty:
            scaler = joblib.load("scaler.pkl")
            cls = int(cognitive_model.predict(scaler.transform(combined.values))[0])
            ai_pred = "IMPAIRED" if cls == 0 else "HEALTHY"

    
    generate_pdf_report(
        patient_name,
        week_number,
        det_pred,
        ai_pred,
        data_folder=session_folder
    )

    
    # does sumary exist
    summary_csv = os.path.join(session_folder, "weekly_summary.csv")
    if not os.path.exists(summary_csv):
        with open(summary_csv, "w") as f:
            f.write("Week,Prediction\n")

    # if more than 4 weeks
    df_session = pd.read_csv(summary_csv)
    if len(df_session) >= 4:
        # generate a session‐level monthly report
        generate_monthly_report(patient_name, session_folder)

    # append to week
    with open(summary_csv, "a") as f:
        f.write(f"{week_number},{det_pred}\n")

    # updating root
    root_folder  = os.path.join("deterministic_model_test", patient_name)
    root_summary = os.path.join(root_folder, "weekly_summary.csv")
    save_weekly_summary(patient_name, week_number, det_pred)

    # if more than 4 weeks change root
    df_root = pd.read_csv(root_summary)
    if len(df_root) >= 4:
        generate_monthly_report(patient_name, root_folder)


if __name__ == "__main__":
    while True:
        print("\nWhat would you like to do?")
        print("1. Run New Test (using webcam)")
        print("2. Import Folder of CSV csvs and Generate Report")
        print("3. Exit Program")

        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            # Run test
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

                #  After 7 csv files - a week, create prediction
                if len([f for f in os.listdir(patient_folder) if f.endswith(".csv")]) >= 7:
                    deterministic_prediction = check_weekly_prediction(patient_name)
                    plot_weekly_speed_trend(patient_name)

                    # AI Prediction - unfinished prototype
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
                        # not taking in saccades
                        selected_features = [
                            'Left_Pupil_X', 'Left_Pupil_Y', 'Right_Pupil_X', 'Right_Pupil_Y',
                            'Speed_px_per_sec', 'Speed_mm_per_sec', 'Speed_deg_per_sec',
                            'fixation_duration', 'Blink_Count', 'Blink_Duration'
                        ]
                        combined_df = combined_df[selected_features]
                        scaler = joblib.load('scaler.pkl')
                        features = combined_df.values
                        
                        features_scaled = scaler.transform(features)
                        prediction = cognitive_model.predict(features_scaled)
                        predicted_class = int(prediction[0])
                        ai_prediction = "IMPAIRED" if predicted_class == 0 else "HEALTHY"


                    # Generate PDF report
                    week_number = len([f for f in os.listdir(patient_folder) if f.endswith(".csv")]) // 7
                    if deterministic_prediction is not None and ai_prediction is not None:
                        generate_pdf_report(patient_name, week_number, deterministic_prediction, ai_prediction, patient_folder)
                        save_weekly_summary(patient_name, week_number, deterministic_prediction)

                    if len([f for f in os.listdir(patient_folder) if f.endswith(".csv")]) >= 28:
                        generate_monthly_report(patient_name)
            else:
                print("Error: Patient name cannot be empty.")

        elif choice == "2":
            # Import csvs
            folder_to_import = input("Enter path to folder containing CSV csvs: ").strip()
            target_patient_name = input("Enter target patient name: ").strip()

            import_existing_data_and_generate_report(target_patient_name, folder_to_import)

        elif choice == "3":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select 1, 2, or 3.")