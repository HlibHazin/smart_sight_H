from typing import Tuple

import numpy as np
import cv2

DEFAULT_ARUCO_DICT = cv2.aruco.DICT_4X4_50


class ArucoDetector:
    """Class detects ArUco markers on image.
    """
    def __init__(
        self, camera_mtx: np.ndarray, dist: np.ndarray, marker_size: float,
        aruco_dict: int = DEFAULT_ARUCO_DICT
    ) -> None:
        """

        Args:
            camera_mtx (np.ndarray): intrinsic camera matrix [3, 3]
            dist (np.ndarray): distortion coefficients [1, 5]
            marker_size (float): marker size in meters
            aruco_dict (int, optional): aruco dict number. Defaults to cv2.aruco.DICT_4X4_50.
        """
        dictionary = cv2.aruco.getPredefinedDictionary(aruco_dict)
        parameters = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(dictionary, parameters)

        self._camera_mtx = camera_mtx
        self._dist = dist
        self._marker_size = marker_size

    def detect(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """ArUco marker detection.

        Args:
            img (np.ndarray): image in BGR color space [H, W, 3]

        Returns:
            Tuple[np.ndarray, np.ndarray]:
                bboxes - For each detected marker, its bounding box are provided.
                    [left, top, right, bottom]. [M, 4]
                ids - vector of identifiers of the detected markers. [M]
        """
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        corners, ids, _ = self._detector.detectMarkers(img_gray)

        bboxes = np.empty((0, 6))
        if corners:
            corners = np.concatenate(corners)
            bboxes = np.concatenate([corners.min(axis=1), corners.max(axis=1), np.ones((corners.shape[0], 2))], axis=1)

        return bboxes
