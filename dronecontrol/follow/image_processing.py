import cv2
import numpy as np
import mediapipe as mp


from dronecontrol.common.utils import Color
from dronecontrol.common import utils
from mediapipe.python.solutions.pose import PoseLandmark


mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


CAMERA_BOX = np.asarray((0, 0)), np.asarray((1, 1))
CORE_LANDMARKS = [
    PoseLandmark.NOSE, 
    PoseLandmark.RIGHT_SHOULDER, 
    PoseLandmark.RIGHT_HIP, 
    PoseLandmark.RIGHT_KNEE, 
    PoseLandmark.RIGHT_ANKLE
]


def detect(results, image):
    """Process detection results into a box matching the bounds of the detected person."""
    if not results.pose_landmarks:
        return CAMERA_BOX[0], CAMERA_BOX[1]

    p1, p2 = get_bounding_box(results.pose_landmarks.landmark)
    error = not is_standing_pose(results, p1, p2)

    size = (image.shape[1], image.shape[0])
    cv2.rectangle(image, (p1 * size).astype(int), (p2 * size).astype(int), 
                  Color.RED if error else Color.BLUE, 2, 1)
    mp_drawing.draw_landmarks(image, results.pose_landmarks, 
                              mp_pose.POSE_CONNECTIONS,
                              landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

    if error:
        return CAMERA_BOX[0], CAMERA_BOX[1]
    else:
        return p1, p2


def get_bounding_box(landmarks):
    """Returns coordinates of a box matching the bounds of the detected person."""
    p1_x = min(landmarks, key=lambda landmark: landmark.x).x
    p2_x = max(landmarks, key=lambda landmark: landmark.x).x
    p1_y = min(landmarks, key=lambda landmark: landmark.y).y
    p2_y = max(landmarks, key=lambda landmark: landmark.y).y

    # Increase box size by 10% in each dimension
    diff = np.asarray(((p2_x - p1_x) * 0.1, (p2_y - p1_y) * 0.1))
    return np.asarray((p1_x, p1_y)) - diff, np.asarray((p2_x, p2_y)) + diff


def is_standing_pose(results, p1, p2):
    """Return whether the bounding box provided matches the pose of a standing person."""
    core_points = [results.pose_landmarks.landmark[i] for i in CORE_LANDMARKS]
    height = p2[1] - p1[1]
    width = p2[0] - p1[0]

    is_standing = all(core_points[i].y <= core_points[i+1].y for i in range(len(core_points) - 1))
    is_standing &= height > width
    return is_standing
