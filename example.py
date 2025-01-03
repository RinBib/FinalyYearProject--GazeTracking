import cv2
from gaze_tracking import GazeTracking
from gaze_tracking.fixation import FixationDetector

# Initialize GazeTracking and FixationDetector
gaze = GazeTracking()
fixation_detector = FixationDetector(threshold=10, duration=0.5)

webcam = cv2.VideoCapture(0)

while True:
    # Read a frame from the webcam
    _, frame = webcam.read()
    gaze.refresh(frame)

    # Get current pupil positions
    left_pupil = gaze.pupil_left_coords()
    right_pupil = gaze.pupil_right_coords()

    # Calculate the average pupil position (midpoint between left and right pupils)
    if left_pupil and right_pupil:
        current_position = ((left_pupil[0] + right_pupil[0]) / 2,
                            (left_pupil[1] + right_pupil[1]) / 2)
    else:
        current_position = None

    # Detect fixation
    fixation_detected, fixation_position = fixation_detector.detect_fixation(current_position)

    # Add text overlay to the frame
    frame = gaze.annotated_frame()
    text_lines = []

    # Gaze status
    if gaze.is_blinking():
        text_lines.append("Status: Blinking")
    elif gaze.is_right():
        text_lines.append("Status: Looking right")
    elif gaze.is_left():
        text_lines.append("Status: Looking left")
    elif gaze.is_center():
        text_lines.append("Status: Looking center")
    else:
        text_lines.append("Status: Unknown")

    # Add pupil coordinates
    if left_pupil:
        text_lines.append(f"Left Pupil: {left_pupil}")
    if right_pupil:
        text_lines.append(f"Right Pupil: {right_pupil}")

    # Add fixation coordinates if detected
    if fixation_detected:
        text_lines.append(f"Fixation: {fixation_position}")
    else:
        text_lines.append("Fixation: None")

    # Render all text lines on the frame
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_color = (255, 255, 255)  # White
    thickness = 1
    y_offset = 20  # Initial y-coordinate for text

    for line in text_lines:
        position = (10, y_offset)
        cv2.putText(frame, line, position, font, font_scale, font_color, thickness, cv2.LINE_AA)
        y_offset += 20  # Increment y-coordinate for the next line

    # Display the annotated frame
    cv2.imshow("Frame", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

webcam.release()
cv2.destroyAllWindows()
