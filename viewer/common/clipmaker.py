import logging
import os
import queue
import time
from datetime import datetime
from threading import Lock, Thread

import cv2
import numpy as np


class ClipMaker:
    def __init__(self, src, codec="mp4v", thumbsize=150, workdir=""):
        self.codec = codec
        self.logger = logging.getLogger(__name__)
        self.src = src
        self.started = False
        self.startedAt = 0
        self.thread = None
        self.thumbsize = thumbsize
        self.workdir = workdir if workdir != "" else os.path.sep.join([os.getcwd(), "data"])

    def _makeClip(self):
        clip, clipName = self._openClip()
        self.logger.info("open clip: %s", clipName)

        while self.started and self.src.bufque.qsize():
            try:
                clip.write(self.src.bufque.get())
            except queue.Empty:
                pass
        while self.started and self.src.queuing:
            try:
                clip.write(self.src.bufque.get(timeout=0.01))
            except queue.Empty:
                pass

        self.logger.info("close clip: %s", clipName)
        clip.release()

    def _openClip(self):
        frame = self.src.bufque.get()
        h, w = frame.shape[:2]
        if h < w:
            y1, y2, x1, x2 = 0, h, (w - h)//2, (w + h)//2
        else:
            y1, y2, x1, x2 = (h - w)//2, (h + w)//2, 0, w
        cropped = frame[y1:y2, x1:x2]

        now = datetime.now()
        thumbName = os.path.sep.join([self.workdir, "{}.thumb.jpeg".format(
            now.strftime("%Y%m%d.%H%M%S"))])
        cv2.imwrite(thumbName, cv2.resize(cropped, (self.thumbsize, self.thumbsize)))

        clipNameTpl = "{}.mp4" if self.codec == "mp4v" else "{}.avi"
        clipName = os.path.sep.join([self.workdir, clipNameTpl.format(
            now.strftime("%Y%m%d.%H%M%S"))])

        # fourcc = cv2.VideoWriter_fourcc(*"XVID")
        # fourcc = cv2.VideoWriter_fourcc(*"mp4v") # Be sure to use the lower case
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        return cv2.VideoWriter(clipName, fourcc, 20.0, (w, h)), clipName

    def start(self):
        if self.started:
            return None

        self.src.startQueuing()
        self.startedAt = time.monotonic()
        self.started = True
        self.thread = Thread(target=self._makeClip)
        self.thread.start()
        return self

    def stop(self):
        self.src.stopQueuing()
        self.started = False
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback):
        pass
