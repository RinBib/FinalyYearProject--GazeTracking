from eye_movement import EyeMovementDetector


# Initialize Eye Movement Detector
detector = EyeMovementDetector()

# Process incoming gaze data
gaze_data = []  # Store gaze points over time

def process_gaze_data(x, y, timestamp):
    global gaze_data
    gaze_data.append((x, y, timestamp))  # Add new data point

    # Detect fixations, saccades, and blinks
    fixations = detector.detect_fixations(gaze_data)
    saccades = detector.detect_saccades(gaze_data)
    blinks = detector.detect_blinks(gaze_data)

    # Display results
    print("Fixations:", fixations[-1] if fixations else "No Fixation")
    print("Saccades:", saccades[-1] if saccades else "No Saccade")
    print("Blinks:", blinks[-1] if blinks else "No Blink")

# Example usage (replace with actual gaze input)
process_gaze_data(100, 200, 0)
process_gaze_data(102, 202, 50)
process_gaze_data(101, 201, 100)
