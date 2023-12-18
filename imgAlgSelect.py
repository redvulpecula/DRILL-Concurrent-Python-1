import cv2
import numpy as np

class YOLOProcessor:
    def __init__(self, frames, yolo_model, device, verbose=False):
        self.frames = frames
        self.yolo_model = yolo_model
        self.device = device
        self.verbose = verbose

    def process(self):
        while True:
            frame = self.frames.get()
            
            if frame is None:
                break

            results = self.yolo_model(frame, device=self.device, verbose=self.verbose)
            result = results[0]
            bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
            classes = np.array(result.boxes.cls.cpu(), dtype="int")

            for cls, bbox in zip(classes, bboxes):
                (x, y, x2, y2) = bbox
                cv2.rectangle(frame, (x, y), (x2, y2), (0, 0, 225), 2)
                cv2.putText(frame, str(cls), (x, y - 5), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 225), 2)
            cv2.imshow('YOLO Model', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
