import time

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

from detector.objectdetector import ObjectDetector


img = cv2.imread("resources/zidane.jpg")

detector = ObjectDetector("resources/yolov5n.onnx")

yolov8 = YOLO("resources/yolov8n.pt")
# success = yolov8.export(format="onnx")  # export the model to ONNX format

yolov8(img, verbose=False)
ts = []
for _ in tqdm(range(100)):
    t0 = time.time()
    # detector.detect(img)
    res = yolov8(img, verbose=False)
    t1 = time.time()
    ts.append(t1 - t0)

print(np.mean(ts), 1 / np.mean(ts), np.std(ts))
