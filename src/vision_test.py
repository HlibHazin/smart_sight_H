import cv2
from ultralytics import YOLO

model = YOLO("best.pt")

cap = cv2.VideoCapture(1)

print("Запуск сканера... Нажми ESC для выхода.")

while True:
    ret, frame = cap.read()
    if not ret: 
        print("Не удалось получить кадр с камеры.")
        break
        
    results = model(frame, conf=0.15)
    
    annotated_frame = results[0].plot()
    
    cv2.imshow("Smart Sight - Vision Only", annotated_frame)
    
    if cv2.waitKey(1) == 27: 
        break
        
cap.release()
cv2.destroyAllWindows()