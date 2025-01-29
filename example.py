import cv2
import numpy as np
import os
import csv
from datetime import datetime
from gaze_tracking import GazeTracking
from gaze_tracking.fixation import FixationDetector

# Initialize GazeTracking and FixationDetector
gaze = GazeTracking()
fixation_detector = FixationDetector(threshold=10, duration=0.5)

def initialize_csv(log_file, headers):
    """Initialize the CSV log file."""
    with open(log_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

def log_data(log_file, data):
    """Log gaze data to the CSV file."""
    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)

def generate_filename(participant_name, task_number):
    """Generate a unique filename for each participant and task."""
    filename = f"{participant_name}_Task{task_number}.csv"
    
    # Ensure file doesn't get overwritten
    count = 1
    while os.path.exists(filename):
        filename = f"{participant_name}_Task{task_number}_{count}.csv"
        count += 1
    
    return filename

def task_1_basic_tracking(participant_name):
    """Task 1: Basic Gaze Tracking without Additional Stimuli"""
    log_file = generate_filename(participant_name, 1)
    initialize_csv(log_file, ["Timestamp", "Left_Pupil_X", "Left_Pupil_Y",
                              "Right_Pupil_X", "Right_Pupil_Y", "Fixation_Detected",
                              "Fixation_X", "Fixation_Y"])

    webcam = cv2.VideoCapture(0)
    print(f"Starting Task 1 for {participant_name}. Press 'q' to quit.")

    while True:
        _, frame = webcam.read()
        gaze.refresh(frame)

        # Get current pupil positions
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()

        # Calculate the average pupil position
        current_position = ((left_pupil[0] + right_pupil[0]) / 2,
                            (left_pupil[1] + right_pupil[1]) / 2) if left_pupil and right_pupil else None

        # Detect fixation
        fixation_detected, fixation_position = fixation_detector.detect_fixation(current_position)

        # Log data
        log_data(log_file, [
            datetime.now(),
            *(left_pupil if left_pupil else (None, None)),
            *(right_pupil if right_pupil else (None, None)),
            fixation_detected,
            *(fixation_position if fixation_position else (None, None))
        ])

        # Annotate frame
        frame = gaze.annotated_frame()
        cv2.putText(frame, f"Task 1: {participant_name}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f"Task 1: {participant_name}", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()
    print(f"Task 1 for {participant_name} completed. Data saved to {log_file}")

def task_2_controlled_stimulus(participant_name):
    """Task 2: Controlled Stimulus Tracking"""
    log_file = generate_filename(participant_name, 2)
    initialize_csv(log_file, ["Timestamp", "Left_Pupil_X", "Left_Pupil_Y",
                              "Right_Pupil_X", "Right_Pupil_Y", "Fixation_Detected",
                              "Fixation_X", "Fixation_Y", "Stimulus_X", "Stimulus_Y"])

    webcam = cv2.VideoCapture(0)
    print(f"Starting Task 2 for {participant_name}. Press 'q' to quit.")

    start_time = cv2.getTickCount() / cv2.getTickFrequency()  # Initialize timer

    while True:
        _, frame = webcam.read()
        gaze.refresh(frame)

        # Calculate elapsed time
        current_time = cv2.getTickCount() / cv2.getTickFrequency()
        time_elapsed = current_time - start_time

        # Generate stimulus
        center_x = int(320 + 100 * np.cos(time_elapsed))  # X-coordinate
        center_y = int(240 + 100 * np.sin(time_elapsed))  # Y-coordinate
        cv2.circle(frame, (center_x, center_y), 20, (0, 255, 255), -1)  # Draw yellow circle
        stimulus_position = (center_x, center_y)

        # Get current pupil positions
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()

        # Calculate the average pupil position
        current_position = ((left_pupil[0] + right_pupil[0]) / 2,
                            (left_pupil[1] + right_pupil[1]) / 2) if left_pupil and right_pupil else None

        # Detect fixation
        fixation_detected, fixation_position = fixation_detector.detect_fixation(current_position)

        # Log data
        log_data(log_file, [
            datetime.now(),
            *(left_pupil if left_pupil else (None, None)),
            *(right_pupil if right_pupil else (None, None)),
            fixation_detected,
            *(fixation_position if fixation_position else (None, None)),
            *stimulus_position
        ])

        # Annotate frame
        frame = gaze.annotated_frame()
        cv2.putText(frame, f"Task 2: {participant_name}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f"Task 2: {participant_name}", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()
    print(f"Task 2 for {participant_name} completed. Data saved to {log_file}")

if __name__ == "__main__":
    print("Select a task to run:")
    print("1. Task 1: Basic Gaze Tracking")
    print("2. Task 2: Controlled Stimulus Tracking")
    
    task = input("Enter 1 or 2: ").strip()

    if task not in ["1", "2"]:
        print("Invalid selection. Exiting.")
        exit()

    # Prompt user for participant's name
    participant_name = input("Enter the name of the test participant: ").strip()
    if not participant_name:
        print("Participant name cannot be empty.")
        exit()

    # Run the selected task with the given participant name
    if task == "1":
        task_1_basic_tracking(participant_name)
    elif task == "2":
        task_2_controlled_stimulus(participant_name)
