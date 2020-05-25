import logging
import queue
import time
from threading import Lock, Thread

import cv2
import numpy as np


class BufferedVideoStream:
    def __init__(self, src, depth=300):
        self.buffer = None
        self.depth = depth
        self.logger = logging.getLogger(__name__)
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        self.started = False
        self.bufLock = Lock()
        self.readLock = Lock()
        self.queuing = False
        self.bufque = queue.Queue()

        self.start()

    def grab(self):
        self.buffer = []
        frameSize = self.frame.shape[:3]
        ringBuffer = np.zeros((2*self.depth,) + frameSize, dtype=np.uint8)
        frameCounter = 0
        filled = False
        while self.started:
            (grabbed, frame) = self.stream.read()

            if self.queuing:
                self.bufque.put(frame)

            idx = frameCounter % self.depth
            frameCounter += 1
            if frameCounter == self.depth:
                frameCounter = 0
                filled = True

            self.readLock.acquire()
            self.grabbed, self.frame = grabbed, frame
            self.readLock.release()
            self.bufLock.acquire()
            ringBuffer[idx] = ringBuffer[idx + self.depth] = frame
            if not filled:
                self.buffer = ringBuffer[:idx + 1]
            else:
                self.buffer = ringBuffer[idx + 1: idx + 1 + self.depth]
            self.bufLock.release()
            time.sleep(0.04)

    def startQueuing(self):
        self.bufLock.acquire()
        with self.bufque.mutex:
            self.bufque.queue = queue.deque(self.buffer)
            self.queuing = True
        self.bufLock.release()

    def stopQueuing(self):
        self.queuing = False

    def isOpened(self):
        return self.stream.isOpened()

    def read(self):
        self.readLock.acquire()
        frame = self.frame.copy()
        self.readLock.release()
        return True, frame

    def release(self):
        self.stop()
        return self.stream.release()

    def start(self):
        if self.started:
            return None
        self.started = True
        self.thread = Thread(target=self.grab, args=())
        self.thread.start()
        return self

    def stop(self):
        self.started = False
        if self.thread.is_alive():
            self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stream.release()
