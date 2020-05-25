import logging
import os
import pickle
import time
from datetime import datetime
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
            if p.name != card.name and p.proba > card.proba:
                # use prev values if prev probability was better
                return Card(p.name, p.proba, card.proba, card.rect, card.img, card.time)
            break
    return card


class FaceRecognizer:
    def __init__(self, src,
                 detector="models",
                 model="openface_nn4.small2.v1.t7",
                 recognizer="recognizer.pickle",
                 labelEncoder="le.pickle",
                 detectorConfidence=0.5,
                 getActionLevel=lambda: 0):

        self.logger = logging.getLogger(__name__)
        self.started = False

        self.src = src
        self.detector, self.embedder, self.recognizer, self.lencoder = self._loadRecognizer(
            detector, model, recognizer, labelEncoder)
        self.confidence = detectorConfidence
        self.getActionLevel = getActionLevel
        self.frame = None
        self.lock = Lock()
        self.trackedCards = []

        self.start()

    def _loadRecognizer(self, detector, model, recognizer, labelEncoder):
        # load serialized face detector from disk
        protoPath = os.path.sep.join([detector, "deploy.prototxt"])
        modelPath = os.path.sep.join([detector, "res10_300x300_ssd_iter_140000.caffemodel"])
        d = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

        # load serialized face embedding model from disk
        m = cv2.dnn.readNetFromTorch(model)

        # load the actual face recognition model along with the label encoder
        r = pickle.loads(open(recognizer, "rb").read())
        l = pickle.loads(open(labelEncoder, "rb").read())
        return d, m, r, l

    def _recognizeFrame(self, frame):
        # resize image, then use for getting blob
        frameSized = cv2.resize(frame, (300, 300))

        # construct a blob from the image
        imageBlob = cv2.dnn.blobFromImage(
            frameSized, 1.0, (300, 300), (104.0, 177.0, 123.0), swapRB=False, crop=False)

        # apply OpenCV's deep learning-based face detector to localize
        # faces in the input image
        self.detector.setInput(imageBlob)
        detections = self.detector.forward()

        frameCards = []
        frameH, frameW = frame.shape[:2]
        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with
            # the prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections
            if confidence > self.confidence:
                # compute the (x, y)-coordinates of the bounding box for
                # the face
                box = detections[0, 0, i, 3:7] * np.array([frameW, frameH, frameW, frameH])
                startX, startY, endX, endY = box.astype("int")

                b = 40
                sY = startY-b if startY-b > 0 else 0
                eY = endY+b if endY+b <= frameH else frameH
                sX = startX-b if startX-b > 0 else 0
                eX = endX+b if endX+b <= frameW else frameW
                cardImg = frame[sY:eY, sX:eX]

                card = Card("", 0, 0, (startX, startY, endX, endY), cardImg, datetime.now())
                if self.getActionLevel() == 2:

                    # extract the face ROI
                    face = frame[startY:endY, startX:endX]
                    fH, fW = face.shape[:2]

                    # ensure the face width and height are sufficiently large
                    if fW < 20 or fH < 20:
                        continue

                    # construct a blob for the face ROI, then pass the blob
                    # through our face embedding model to obtain the 128-d
                    # quantification of the face
                    faceBlob = cv2.dnn.blobFromImage(
                        face, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
                    self.embedder.setInput(faceBlob)
                    vec = self.embedder.forward()

                    # perform classification to recognize the face
                    preds = self.recognizer.predict_proba(vec)[0]
                    j = np.argmax(preds)
                    proba = preds[j]
                    name = self.lencoder.classes_[j]

                    card = Card(name, proba, proba, (startX, startY, endX, endY), cardImg, datetime.now())
                    card = lookupTracked(self.trackedCards, card)

                frameCards.append(card)
        return frameCards

    def _main(self):
        # start the FPS throughput estimator
        fps = FPS().start()
        self.trackedCards = []
        while self.started:
            t0 = time.monotonic()
            if self.getActionLevel() > 0:
                _, frame = self.src.read()
                self.lock.acquire()
                self.frame = frame
                self.lock.release()
                cards = self._recognizeFrame(frame)
                self.lock.acquire()
                self.trackedCards = cards
                self.lock.release()
            # update the FPS counter
            fps.update()
            # limit FPS ~5 for reduce CPU utilization
            ts = 0.2 - (time.monotonic() - t0)
            if ts > 0:
                time.sleep(ts)

        # stop the timer and display FPS information
        fps.stop()
        self.logger.info("elapsed time: {:.2f}".format(fps.elapsed()))
        self.logger.info("approx FPS: {:.2f}".format(fps.fps()))

    def getFrameCards(self):
        self.lock.acquire()
        cards = self.trackedCards.copy()
        frame = self.frame.copy()
        self.lock.release()
        return frame, cards

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
