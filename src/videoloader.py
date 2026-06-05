from __future__ import annotations
from typing import Union, Tuple
import sys

import numpy as np
import cv2


class VideoLoader:
    """Class to load a video file or stream from device.
    """
    def __init__(self, video_path: Union[str, int], **kwargs) -> None:
        """

        Args:
            video_path (Union[str, int]): path to video or device number.
            resolution (tuple): frame resolution (W, H)
            exposure_ms (int): camera exposure time in ms
        """
        self._video_path = video_path

        self.frame_count = -1
        if isinstance(video_path, int) and sys.platform.startswith('win'):
            self.cap = self._open_camera_index(video_path)
        elif sys.platform.startswith('win'):
            self.cap = cv2.VideoCapture(self._video_path, cv2.CAP_DSHOW)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
        else:
            self.cap = cv2.VideoCapture(self._video_path)

        exposure_ms = kwargs.get("exposure_ms")
        if exposure_ms is not None and exposure_ms > 0 and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, float(exposure_ms))

        resolution = kwargs.get("resolution")
        if resolution is None:
            self.w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        else:
            self.w, self.h = resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)

        self.n_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Discard a few initial frames to let the camera settle and avoid first-frame noise.
        for _ in range(5):
            if not self.cap.isOpened():
                break
            self.cap.read()

    def __iter__(self) -> VideoLoader:
        self.frame_count = -1
        return self

    def __next__(self) -> np.ndarray:
        """Return next frame in BGR color space.

        Raises:
            StopIteration: in case of the ending of the video or some troubles with the stream.

        Returns:
            np.ndarray: frame in BGR format.
        """
        if self.frame_count >= self.n_frames and self.n_frames > 0:
            raise StopIteration

        if not self.cap.isOpened():
            raise StopIteration

        ret, frame = self.cap.read()
        self.frame_count += 1
        if not ret:
            self.cap.release()
            raise StopIteration

        return frame

    def __len__(self) -> int:
        """number of frames in the video or -1 in case of a stream.

        Returns:
            int: number of frames
        """
        return self.n_frames  # number of files

    def release(self) -> None:
        """Release the VideoCapture class.
        """
        self.cap.release()

    def image_shape(self) -> Tuple[int, int]:
        return self.h, self.w

    def _open_camera_index(self, index: int) -> cv2.VideoCapture:
        """Open a working camera device index on Windows."""
        for candidate in range(index, index + 3):
            cap = cv2.VideoCapture(candidate, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                continue

            cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            self._discard_warmup_frames(cap)
            ret, frame = cap.read()
            if ret and self._is_good_frame(frame):
                if candidate != index:
                    print(f"Warning: camera index {index} produced invalid frames, using index {candidate} instead.")
                return cap

            cap.release()

        print(f"Warning: could not find a good camera starting from index {index}. Using index {index}.")
        return cv2.VideoCapture(index, cv2.CAP_DSHOW)

    @staticmethod
    def _discard_warmup_frames(cap: cv2.VideoCapture, count: int = 5) -> None:
        for _ in range(count):
            if not cap.isOpened():
                break
            cap.read()

    @staticmethod
    def _is_good_frame(frame: np.ndarray) -> bool:
        if frame is None or frame.size == 0:
            return False
        if frame.ndim != 3:
            return False
        mean = float(frame.mean())
        std = float(frame.std())
        return not (mean < 10.0 and std < 5.0)
