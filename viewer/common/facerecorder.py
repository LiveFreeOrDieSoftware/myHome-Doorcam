import logging
import os
import queue
import time
from threading import Lock, Thread

import cv2
import numpy as np
from imutils.video import FPS

from common.card import Card, cardsOverlap


def lookupTracked(trackedCards, card):
    # look into known cards
    for p in trackedCards:
        # find correspond card by area
        if cardsOverlap(p, card):
            if p.proba0:
                if p.proba0 > card.proba0:
                    return p
            else:
                sp = (p.rect[2] - p.rect[0]) * (p.rect[3] - p.rect[1])
                sc = (card.rect[2] - card.rect[0]) * (card.rect[3] - card.rect[1])
                return p if sp > sc else card
    return card


class FaceRecorder:
    def __init__(self, path=""):
        self.logger = logging.getLogger(__name__)
        self.started = False

        self.path = path
        self.lock = Lock()
        self.cards = []
        self.queue = queue.Queue()

        self.start()

    def _main(self):
        while self.started:
            self._q()
            # process queue once per N seconds
            time.sleep(5)

    def _q(self):
        cur, prev = [], []
        while self.queue.qsize():
            try:
                cur = []
                for card in self.queue.get():
                    cur.append(lookupTracked(prev, card))
                prev = cur
            except queue.Empty:
                pass

        for card in cur:
            fname = os.path.sep.join([self.path, "{}.fd.jpeg".format(
                card.time.strftime("%Y%m%d.%H%M%S"))])
            cv2.imwrite(fname, card.img)
            self.logger.info("write face: %s", fname)

    def storeFrameCards(self, frame, cards):
        self.queue.put(cards)

    def start(self):
        if self.started:
            return None
        self.started = True
        self.thread = Thread(target=self._main, args=())
        self.thread.start()
        return self

    def stop(self):
        self.started = False
        if self.thread.is_alive():
            self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback):
        pass
