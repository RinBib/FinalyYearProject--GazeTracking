
import time

class FixationDetector:
    def __init__(self, threshold=10, duration=0.5):
        """
        Initialize the fixation detector.
        
        Parameters:
        - threshold: Maximum allowable distance for fixation (in pixels or coordinates).
        - duration: Minimum time (in seconds) required to classify as fixation.
        """
        self.threshold = threshold
        self.duration = duration
        self.fixation_start_time = None
        self.previous_position = None

    def detect_fixation(self, current_position):
        """
        Detects fixation based on the current pupil position.
        
        Parameters:
        - current_position: Tuple of (x, y) coordinates of the pupil's position.
        
        Returns:
        - fixation_detected: Boolean indicating whether a fixation is detected.
        - fixation_position: Coordinates of the fixation point if detected, None otherwise.
        """
        if not current_position:
            self.fixation_start_time = None
            return False, None

        if self.previous_position:
            # Calculate distance between previous and current position
            distance = ((current_position[0] - self.previous_position[0]) ** 2 +
                        (current_position[1] - self.previous_position[1]) ** 2) ** 0.5

            if distance < self.threshold:
                if not self.fixation_start_time:
                    self.fixation_start_time = time.time()
                elif time.time() - self.fixation_start_time > self.duration:
                    return True, current_position
            else:
                self.fixation_start_time = None

        self.previous_position = current_position
        return False, None
