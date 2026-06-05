import numpy as np


def calc_center(bbox: np.ndarray):

    # compute and draw the center (x, y)-coordinates of the ArUco
    # marker
    cX = int(np.mean(bbox[[0, 2]]))
    cY = int(np.mean(bbox[[1, 3]]))

    return cX, cY


def calc_len(bbox: np.ndarray):

    # compute and draw the center (x, y)-coordinates of the ArUco
    # marker
    lX = abs(int(bbox[0] - bbox[2]))
    lY = abs(int(bbox[1] - bbox[3]))

    return lX, lY
