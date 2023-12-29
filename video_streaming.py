import cv2
import time
from multiprocessing import Process
import socket
from urllib.parse import urlparse

class VideoStream:
    def __init__(self, url, frames):
        self.frames = frames
        self.url = url
        self.process = Process(target=self.capture, args=(self.frames, self.url))
        self.process.start()

    def capture(self, frames, url):
        cap = cv2.VideoCapture(url)
        error_reported = False
        last_success_time = time.time()
        video_count = 0  
        initial_connection_made = False  

        while True:
            ret, frame = cap.read()
            if not ret:
                if time.time() - last_success_time > 60:
                    print("Cannot connect to stream for more than 1 minute. Exiting.")
                    break
                if not error_reported:
                    if initial_connection_made:  
                        video_count += 1  
                        print(f"Finished streaming video number {video_count}.")
                    print("Attempting to reconnect to the next video...")
                    error_reported = True
                    last_success_time = time.time()  
                cap.release()
                cap = cv2.VideoCapture(url)
                continue
            
            if not initial_connection_made:
                initial_connection_made = True 

            error_reported = False
            if not frames.full():
                frames.put(frame)


    def get_frame(self):
        if not self.frames.empty():
            return self.frames.get()

    def release(self):
        self.process.terminate()
        self.process.join()

def check_rtsp_url(url):
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 554 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except socket.error:
        return False

def read_url_from_file(file_path='source.txt'):
    with open(file_path, 'r') as file:
        return file.readline().strip()

def calculate_fps(prev_time, fps):
    while True:
        curr_time = time.time()
        time_diff = curr_time - prev_time
        if time_diff != 0:  # Avoid divide by 0 error
            fps.value = 1 / time_diff
        prev_time = curr_time

def display_fps(frame, fps_async, fps_stream):
    cv2.putText(frame, f'Async FPS: {fps_async.value:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2); cv2.putText(frame, f'Stream FPS: {fps_stream.value:.2f}', (frame.shape[1] - cv2.getTextSize(f'Stream FPS: {fps_stream.value:.2f}', cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0][0] - 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

def display_and_save_frame(fps_async, fps_stream, frames):
    prev_time = time.time()
    while True:
        frame = frames.get()
        if frame is None:
                break
        curr_time = time.time()
        time_diff = curr_time - prev_time
        if time_diff != 0:
            fps_stream.value = 1 / time_diff
        prev_time = curr_time
        display_fps(frame, fps_async, fps_stream)
        cv2.imshow('RTSP Stream', frame)
        if cv2.getWindowProperty('RTSP Stream', cv2.WND_PROP_VISIBLE) < 1:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        