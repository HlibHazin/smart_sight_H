import argparse
import glob
import os
from typing import List, Tuple

import numpy as np
import cv2
import pandas as pd


# Defining the dimensions of checkerboard
CHECKERBOARD = (9, 6)


def calibrate(imgs: List[np.ndarray]) -> Tuple[float, np.ndarray, np.ndarray]:
    """Calibrate camera using list of images.

    Args:
        List[np.ndarray]: calibration images.

    Returns:
        Tuple[float, np.ndarray, np.ndarray]:
            ret - reprojection error
            mtx - intrinsic matrix
            dist - distortion coefficients
    """
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Creating vector to store vectors of 3D points for each checkerboard image
    objpoints = []
    # Creating vector to store vectors of 2D points for each checkerboard image
    imgpoints = []

    # Defining the world coordinates for 3D points
    objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[0, :, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

    for img in imgs:
        # Find the chess board corners
        # If desired number of corners are found in the image then ret = true
        ret, corners = cv2.findChessboardCorners(
            img, CHECKERBOARD, None
        )

        """
        If desired number of corner are detected,
        we refine the pixel coordinates and display
        them on the images of checker board
        """
        if ret == True:
            objpoints.append(objp)
            # refining pixel coordinates for given 2d points.
            corners2 = cv2.cornerSubPix(img, corners, (11, 11), (-1, -1), criteria)

            imgpoints.append(corners2)
        else:
            print('no ret')

    """
    Performing camera calibration by
    passing the value of known 3D points (objpoints)
    and corresponding pixel coordinates of the
    detected corners (imgpoints)
    """
    ret, mtx, dist, _, _ = cv2.calibrateCamera(
        objpoints, imgpoints, img.shape[::-1], None, None)
    return ret, mtx, dist


def read_video(video_path: str) -> List[np.ndarray]:
    """Read video file and take one frame per second.

    Args:
        video_path (str): path to videofile.

    Returns:
        List[np.ndarray]: list of frames from the video.
    """
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    frames = []
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        count += 1
        if count % fps == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    cap.release()

    return frames


def read_imgs(imgs_path: str) -> List[np.ndarray]:
    """Read images from the folder.

    Args:
        imgs_path (str): path to folder with images.

    Returns:
        List[np.ndarray]: list of images.
    """
    paths = sorted(glob.glob(f"{imgs_path}/*"))
    imgs = []
    for p in paths:
        imgs.append(cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY))

    return imgs


def main(ipath: str, opath: str) -> None:
    """Camera calibration using a set of images of video with a checkerboard.
    The intrinsic parameters are saved to the file.

    Args:
        ipath (str): path to images or video.
        opath (str): path to csv file to store parameters.
    """
    if os.path.isdir(ipath):
        imgs = read_imgs(ipath)
    else:
        imgs = read_video(ipath)

    ret, mtx, dist = calibrate(imgs)

    output = {
        'ret': ret,
        'fx': mtx[0, 0],
        'fy': mtx[1, 1],
        'cx': mtx[0, 2],
        'cy': mtx[1, 2],
        'k1': dist[0, 0],
        'k2': dist[0, 1],
        'p1': dist[0, 2],
        'p2': dist[0, 3],
        'k3': dist[0, 4]
    }
    pd.DataFrame(output, index=[0]).to_csv(opath, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Camera callibration')
    parser.add_argument(
        "-i", required=True,
        help="Path to images folder or video file."
    )
    parser.add_argument(
        "-o", default="params.csv",
        help="Path to save csv file with camera parameters."
    )
    args = parser.parse_args()

    main(args.i, args.o)
