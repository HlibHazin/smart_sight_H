import time
from threading import Thread

import numpy as np
import cv2


from servo import ServoWorker, ServoCommands
from statemanger import StateManager
from shotworker import ShotWorker
from utils import calc_center, calc_len
from utilsdraw import draw_sight, draw_bbox


font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 0.7
color = (0, 255, 0)
thickness = 2


class MainLoop:
    def __init__(
        self,
        dataloader,
        detector,
        tracker,
        sight,
        detection_period=2,
        yaw_ths=(2, 3),
        pitch_ths=(2, 3),
        stop_th=7,
        servo_port=None,
    ):
        self._dataloader = dataloader
        self._detector = detector
        self._tracker = tracker

        self._shot_worker = ShotWorker()
        self._shot_thread = Thread(target=self._shot_worker.shot_worker)
        self._shot_thread.start()

        # WORKERS
        self._servo_worker = ServoWorker(servo_port)
        self._state_manager = StateManager(on_enter=self._shot_worker.do_shot)

        # OPTICAL FLOW
        # Parameters for ShiTomasi corner detection
        self._feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)

        # Parameters for Lucas Kanade optical flow
        self._lk_params = dict(
            winSize=(15, 15),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
        )
        self._old_gray = None

        self._frame_count = 0
        self._detection_period = detection_period

        self._yaw_moving_ths = yaw_ths
        self._pitch_moving_ths = pitch_ths
        self._stop_th = stop_th

        self._h, self._w = dataloader.image_shape()
        self._sight = sight

        self._current_id = -1
        self._on_target_prev = False
        self._moving_count = 0
        self._stop_count = 0

    def run(self):
        try:
            ts = [0]
            t_prev = 0
            t = 0

            for frame in self._dataloader:
                # fps
                if t > 0 and t_prev > 0:
                    ts.append(t - t_prev)
                t_prev = t
                t = time.time()

                optical_flow_delta = self._optical_flow(frame)
                optical_flow_delta = [optical_flow_delta[0] * 1.5, optical_flow_delta[1]]

                raw_bboxes = self._detection(frame)
                is_detected = len(raw_bboxes) > 0
                
                bboxes = self._tracking(raw_bboxes.copy(), optical_flow_delta)

                bbox = []
                detected_name = "Unknown" 
                
                if not hasattr(self, 'track_classes'):
                    self.track_classes = {}

                if len(bboxes) > 0:
                    bbox, idx = self._select_box_and_id(bboxes)
                    bbox_center = calc_center(bbox[:4])
                    
                    if len(raw_bboxes) > 0:
                        class_id = 0
                        for raw_box in raw_bboxes:
                            if abs(bbox[0] - raw_box[0]) < 50 and abs(bbox[1] - raw_box[1]) < 50:
                                class_id = int(raw_box[5])
                                break
                        
                        if class_id == 1:
                            detected_name = "Stone"
                        elif 2 <= class_id <= 10:
                            detected_name = "Disease"
                        elif 11 <= class_id <= 25:
                            detected_name = "Weed"
                        else:
                            detected_name = "Unknown"
                            
                        self.track_classes[idx] = detected_name
                    else:
                        detected_name = self.track_classes.get(idx, "Unknown")

                    draw_bbox(frame, bbox[:4], bbox_center, marker_id=idx, class_name=detected_name)

                self._update_state(bbox, optical_flow_delta, class_name=detected_name)

                self._update_servo()

                self._draw_info(frame)

                draw_sight(frame, *self._sight)

                msg = f"detected: {is_detected} | {optical_flow_delta}"

                cv2.imwrite(f"debug/{self._frame_count:04}.png", frame)

                # Display the resulting frame
                cv2.imshow('ArUco Detector', frame)

                if len(ts) == 10:
                    # print(f"FPS = {1 / np.mean(ts):.02f}")
                    ts = []
                if cv2.waitKey(1) == 27 or self._state_manager.exit:
                    self._shot_worker.stop_shot_worker = True
                    break
        finally:
            self._servo_worker.join()
            self._state_manager.join()
            self._shot_worker.stop_shot_worker = True
            self._shot_thread.join()

    def _detection(self, frame):
        if not self._frame_count % self._detection_period:
            bboxes = self._detector.detect(frame)
        else:
            bboxes = np.empty((0, 6)) 
        self._frame_count += 1

        return bboxes

    def _tracking(self, bboxes, camera_shift):
        return self._tracker.update(bboxes, camera_shift)

    def _optical_flow(self, frame):
        delta = [0, 0]

        good_new = []
        good_old = []
        frame_gray = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY)
        if self._old_gray is not None:
            # Calculate Optical Flow
            p0 = cv2.goodFeaturesToTrack(self._old_gray, mask=None, **self._feature_params)
            if p0 is not None and len(p0):
                p1, st, err = cv2.calcOpticalFlowPyrLK(
                    self._old_gray, frame_gray, p0, None, **self._lk_params
                )
                # Select good points
                good_new = p1[st == 1]
                good_old = p0[st == 1]

            if len(good_new) and len(good_old):
                delta = np.median(good_new - good_old, axis=0).astype(int)
                delta[0] *= 1.5
            else:
                delta = [0, 0]
        self._old_gray = frame_gray

        return delta

    def _update_by_camera_shift(self, bboxes, shift):
        upd_boxes = bboxes.copy()
        upd_boxes[:, [0, 2]] = np.clip(upd_boxes[:, [0, 2]] + shift[0], 0, self._w)
        upd_boxes[:, [1, 3]] = np.clip(upd_boxes[:, [1, 3]] + shift[1], 0, self._h)

        return upd_boxes

    def _update_servo(self):
        self._servo_worker.update(
            self._state_manager.yaw,
            self._state_manager.pitch
        )

    def _draw_info(self, frame):
        mode_str = "M" if self._state_manager.manual_mode else "A"
        msg = f"mode: {mode_str}"
        cv2.putText(frame, msg, (10, 470), font, fontScale, color, thickness, cv2.LINE_AA)

        msg = f"yaw: {self._state_manager.yaw.name} pitch: {self._state_manager.pitch.name}"
        cv2.putText(frame, msg, (10, 30), font, fontScale, color, thickness, cv2.LINE_AA)

        msg = f"servo port: {getattr(self._servo_worker, 'process', None) is not None}"
        # cv2.putText(frame, msg, (10, 60), font, fontScale, color, thickness, cv2.LINE_AA)

    def _select_box_and_id(self, bboxes):
        ids = bboxes[:, -1]
        if self._current_id not in ids:
            self._current_id = ids[0]

        bbox = bboxes[ids == self._current_id][0]

        return bbox, self._current_id

    def _update_state(self, bbox, camera_shift, class_name="Unknown"):
        pitch_idx = 0
        yaw_idx = 0
        
        
        if class_name == "Stone" and not self._state_manager.manual_mode:
            self._state_manager.yaw = ServoCommands.IGNORE
            self._state_manager.pitch = ServoCommands.IGNORE
            self._moving_count = 0 
            return

        if len(bbox):
            target_pos = calc_center(bbox[:4])
            x_diff = target_pos[0] - self._sight[0]
            y_diff = target_pos[1] - self._sight[1]

            lx, ly = calc_len(bbox[:4])
            K = 0.3
            lx = int(lx * K)
            ly = int(ly * K)

            if np.abs(x_diff) > 2 * lx:
                yaw_idx = 1

            if np.abs(y_diff) > 2 * ly:
                pitch_idx = 1

            if not self._state_manager.manual_mode:

                if self._moving_count <= self._yaw_moving_ths[yaw_idx]:
                    if x_diff > lx:
                        self._state_manager.yaw = ServoCommands.INC
                    elif x_diff < -lx:
                        self._state_manager.yaw = ServoCommands.DEC
                    else:
                        self._state_manager.yaw = ServoCommands.STOP

                if self._moving_count <= self._pitch_moving_ths[pitch_idx]:
                    if y_diff > ly:
                        self._state_manager.pitch = ServoCommands.INC
                    elif y_diff < -ly:
                        self._state_manager.pitch = ServoCommands.DEC
                    else:
                        self._state_manager.pitch = ServoCommands.STOP

                if np.abs(x_diff) < lx and np.abs(y_diff) < ly:
                    on_target = True
                else:
                    on_target = False

                if np.linalg.norm(camera_shift) < 20:
                    if on_target and self._on_target_prev is False:
                        self._shot_worker.do_shot()
                else:
                    on_target = False

                self._on_target_prev = on_target
        else:
            if not self._state_manager.manual_mode:
                self._state_manager.yaw = ServoCommands.STOP
                self._state_manager.pitch = ServoCommands.STOP

        if not self._state_manager.manual_mode:
            if self._state_manager.yaw == ServoCommands.STOP and self._state_manager.pitch == ServoCommands.STOP:
                self._stop_count += 1
            else:
                self._moving_count += 1

            if self._moving_count >= self._pitch_moving_ths[pitch_idx]:
                self._state_manager.pitch = ServoCommands.STOP
            if self._moving_count >= self._yaw_moving_ths[yaw_idx]:
                self._state_manager.yaw = ServoCommands.STOP

            if self._stop_count > self._stop_th:
                self._moving_count = 0
                self._stop_count = 0
        else:
            self._moving_count = 0

        if self._shot_worker.state_updated:
            self._shot_worker.state_updated = False
            if self._shot_worker.make_shot:
                self._state_manager.yaw = ServoCommands.LASER_ON
            else:
                self._state_manager.yaw = ServoCommands.LASER_OFF
            self._state_manager.pitch = ServoCommands.IGNORE
