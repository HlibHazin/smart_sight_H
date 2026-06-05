import cv2
import numpy as np


def draw_sight(img: np.ndarray, x: int, y: int) -> None:
    color = (0, 255, 0)
    shift0 = 15
    shift1 = 75
    thickness = 2

    # cv2.circle(img, (x, y), 1, color, -1)
    cv2.line(img, (x - shift1, y), (x - shift0, y), color, thickness)
    cv2.line(img, (x + shift0, y), (x + shift1, y), color, thickness)
    cv2.line(img, (x, y - shift1), (x, y - shift0), color, thickness)
    cv2.line(img, (x, y + shift0), (x, y + shift1), color, thickness)
    cv2.circle(img, (x, y), 35, color, thickness)
    cv2.circle(img, (x, y), 60, color, thickness)


def draw_bbox(
    img: np.ndarray, bbox: np.ndarray, center: tuple = None,
    marker_id: int = None, class_name: str = "",
    color: tuple = (255, 0, 0), thickness: int = 2
) -> None:

    bbox = bbox.astype(int)
    cv2.rectangle(img, bbox[:2], bbox[2:], color, thickness)

    label = f"{class_name} ID:{marker_id}" if marker_id is not None else class_name
    
    if label.strip():
        cv2.putText(
            img, label, (bbox[0] + 5, bbox[1] - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, thickness
        )