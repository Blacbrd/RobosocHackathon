from modlib.devices import AiCamera
from modlib.models.zoo import SSDMobileNetV2FPNLite320x320
from modlib.apps import BYTETracker, Annotator
import cv2 as cv
import mediapipe as mp
import time

class HandDetector:
    def __init__(self):
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.finger_coordinates = [(8, 6), (12, 10), (16, 14), (20, 18)]
        
        # Camera initialisation with retry
        self.device = AiCamera()
        self.model = SSDMobileNetV2FPNLite320x320()
        self._init_camera()
        
        # Initialize tracking components
        self.tracker = BYTETracker(BYTETrackerArgs())
        self.annotator = Annotator(
            thickness=1,
            text_thickness=1,
            text_scale=0.4
        )
        self.stream = None

    def _init_camera(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.device.deploy(self.model)
                return
            except RuntimeError as e:
                if "Device or resource busy" in str(e) and attempt < max_retries - 1:
                    print(f"Camera initialization failed - retrying ({attempt+1}/{max_retries})")
                    time.sleep(1.5)
                    self._release_camera()
                else:
                    raise RuntimeError(f"Camera initialization failed permanently: {str(e)}")

    def _release_camera(self):
        try:
            self.device.__exit__(None, None, None)
        except Exception as e:
            print(f"Camera release error: {str(e)}")

    def get_fingers(self):
        try:
            if not self.stream:
                self.stream = self.device.__enter__()
            frame = next(self.stream)
        except (StopIteration, RuntimeError):
            self._release_camera()
            self.stream = self.device.__enter__()
            frame = next(self.stream)
        
        img_bgr = frame.image
        finger_count = 0
        hand_x = None

        if img_bgr is not None:
            # Hand detection processing
            img_rgb = cv.cvtColor(img_bgr, cv.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)
            
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                h, w = img_bgr.shape[:2]
                
                wrist = hand_landmarks.landmark[0]
                hand_x = wrist.x
                
                # Finger counting logic
                hand_points = [(int(lm.x * w), int(lm.y * h)) 
                             for lm in hand_landmarks.landmark]
                for coord in self.finger_coordinates:
                    if hand_points[coord[0]][1] < hand_points[coord[1]][1]:
                        finger_count += 1

        return finger_count, hand_x

    def close(self):
        """Explicit resource cleanup"""
        self._release_camera()
        self.stream = None
        self.hands.close()

class BYTETrackerArgs:
    # Tracker configuration parameters
    track_thresh: float = 0.25
    track_buffer: int = 30
    match_thresh: float = 0.8
    aspect_ratio_thresh: float = 3.0
    min_box_area: float = 1.0
    mot20: bool = False
