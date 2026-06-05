import numpy as np
import ultralytics


class ObjectDetector:
    def __init__(
        self, model_path: str,
        img_size: tuple = (640, 640),
        batch_size: int = 1,
        conf_thres: float = 0.01,
        iou_thres: float = 0.45,
        input_name="images",
        classes=None
    ) -> None:
        self._model = ultralytics.YOLO(model_path)
        self._classes = classes

    def detect(self, frame: np.ndarray) -> np.ndarray:
        pred = self._model(frame, verbose=False)[0]
        pred = self._postprocessing(pred)

        return pred

    def _postprocessing(self, prediction) -> np.ndarray:
        boxes = np.hstack([
            prediction.boxes.xyxy.cpu().numpy(),
            prediction.boxes.conf.cpu().numpy()[:, None],
            prediction.boxes.cls.cpu().numpy()[:, None]
        ])

        return boxes
