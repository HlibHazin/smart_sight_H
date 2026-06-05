import argparse
import os

import pandas as pd
import numpy as np

from videoloader import VideoLoader
from detector.arucodetector import ArucoDetector
from detector.objectdetector import ObjectDetector
from sort.sort import Sort
from mainloop import MainLoop


TRACK_MAX_AGE = 2
TRACK_INIT_TH = 1

ARUCO_MOVING_YAW_THS = 3, 4
ARUCO_MOVING_PITCH_THS = 2, 3
ARUCO_STOP_TH = 18

PERSON_MOVING_YAW_THS = 2, 3
PERSON_MOVING_PITCH_THS = 2, 3
PERSON_STOP_TH = 7

AVAILABLE_CLASSES = {
    "person": 0,
    "cat": 15
}


def main(input_path: str, video_resolution: tuple, params_path: str, is_aruco: bool, **kwargs) -> None:
    # initialization step
    params = pd.read_csv(params_path)

    try:
        input_path = int(input_path)
    except ValueError:
        pass

    servo_port = kwargs.get("servo_port")

    if is_aruco:
        mtx = np.array([
            [params['fx'][0], 0, params['cx'][0]],
            [0, params['fy'][0], params['cy'][0]],
            [0, 0, 1]
        ])
        dist = np.array([params.values[:, -5:]])
        detector = ArucoDetector(mtx, dist, kwargs["marker_size"])
        yaw_ths = ARUCO_MOVING_YAW_THS
        pitch_ths = ARUCO_MOVING_PITCH_THS
        stop_th = ARUCO_STOP_TH
    else:
        detector = ObjectDetector(kwargs["model_path"], conf_thres=kwargs["conf_th"])
        yaw_ths = PERSON_MOVING_YAW_THS
        pitch_ths = PERSON_MOVING_PITCH_THS
        stop_th = PERSON_STOP_TH

    exposure_ms = kwargs.get("exposure_ms", 50)
    dataloader = VideoLoader(input_path, resolution=video_resolution, exposure_ms=exposure_ms)
    tracker = Sort(max_age=TRACK_MAX_AGE, min_hits=TRACK_INIT_TH, return_only_hits=False)

    sight = [int(params['cx'][0]), int(params['cy'][0])]
    # sight = [320, 240]

    main_loop = MainLoop(
        dataloader,
        detector,
        tracker,
        sight,
        yaw_ths=yaw_ths,
        pitch_ths=pitch_ths,
        stop_th=stop_th,
        servo_port=servo_port,
    )
    main_loop.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Detection loop')
    parser.add_argument(
        "--input", default="1",
        help="Path to a video file or index of a camera. Default=1"
    )
    parser.add_argument(
        "--resolution", nargs="+", type=int, default=(640, 480),
        help="Video resolution (W, H). Default=640, 480"
    )
    parser.add_argument(
        "--params",
        default=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "camera_params/logi_c270.csv"),
        help="Path to csv file with camera parameters. Default=camera_params/logi_c270.csv"
    )
    parser.add_argument(
        "--aruco", action='store_true',
        help="Is aruco or object detector. Default=False"
    )
    parser.add_argument(
        "--marker-size", type=float, default=0.1,
        help="Size of ArUco marker in meters. Default=0.1."
    )
    parser.add_argument(
        "--model-path", default="best.pt",
        help="Path to object detection model weights file. Default=best.pt."
   )
    parser.add_argument(
        "--conf-th", type=float, default=0.4,
        help="Object detection model confidence threshold. Default=0.4."
    )
    parser.add_argument(
        "--exposure-ms", type=int, default=0,
        help="Camera exposure in ms. 0 = use the camera's default exposure. Default=0."
    )
    parser.add_argument(
        "--det-cls", default='person',
        help=f"Class name that shold be detected. One of {AVAILABLE_CLASSES}. Default=person."
    )
    parser.add_argument(
        "--servo-port", default=None,
        help="Serial port for the servo controller, e.g. COM3. If omitted, the first available port is used."
    )

    args = parser.parse_args()

    main(
        args.input,
        args.resolution,
        args.params,
        args.aruco,
        marker_size=args.marker_size,
        model_path=args.model_path,
        conf_th=args.conf_th,
        exposure_ms=args.exposure_ms,
        det_cls=args.det_cls,
        servo_port=args.servo_port,
    )
