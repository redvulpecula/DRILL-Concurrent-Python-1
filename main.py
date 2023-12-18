import time
from multiprocessing import Process, Manager
import torch
from ultralytics import YOLO
from video_streaming import VideoStream, calculate_fps, display_and_save_frame, check_rtsp_url, read_url_from_file
from imgAlgSelect import YOLOProcessor

class ConcurrencyManager:
    def __init__(self, url):
        self.device = 'cuda' if torch.backends.cuda.is_built() else 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.yolo_model = YOLO("yolov8m.pt")
        self.manager = Manager()
        self.url = url
        self.frames = self.manager.Queue(maxsize=1)
        self.video_stream = VideoStream(url, self.frames)
        self.fps_async = self.manager.Value('d', 0.0)
        self.fps_stream = self.manager.Value('d', 0.0)

    def start_stream(self):
        print("Waiting for the stream.")
        while not check_rtsp_url(self.url):
            print("Cannot connect to the URL or the port is not open. Retrying.")
        
        p_fps = Process(target=calculate_fps, args=(time.time(), self.fps_async))
        p_fps.start()

        p_display = Process(target=display_and_save_frame, args=(self.fps_async, self.fps_stream, self.video_stream.frames))
        p_display.start()

        p_yolo = Process(target=YOLOProcessor(self.video_stream.frames, self.yolo_model, self.device).process)
        p_yolo.start()

        p_display.join()
        p_fps.join()
        p_yolo.join()
        
        self.video_stream.release()

def main():
    url = read_url_from_file()
    ConcurrencyManager(url).start_stream()

if __name__ == '__main__':
    main()
