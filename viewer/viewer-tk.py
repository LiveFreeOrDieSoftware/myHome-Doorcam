
import argparse
import functools
import glob
import json
import logging
import os
import pickle
import queue
import threading
import time
from collections import namedtuple
from datetime import datetime, timedelta

import cv2
import imutils
import numpy as np

from common.bvstream import BufferedVideoStream
from common.card import Card, cardsOverlap
from common.clipmaker import ClipMaker
from common.facerecognizer import FaceRecognizer
from common.facerecorder import FaceRecorder
from common.fd import extractEmbeddings, trainModel
from common.tkapp import TkApp
from motion.motiondetection import initializeMotionDetection

MDState = namedtuple("MDState", "detected trackedFrame trackedAt lastDetectedAt")


logger = logging.getLogger(__name__)
tkApp = None
initializeMotionDetection()

def getCLIArgs():
    ap = argparse.ArgumentParser()
    ap.add_argument("--action", type=int, default="1", choices=[0, 1, 2],
                    help="action level 0:motion detection, 1:face detection, 2:face recognition")
    ap.add_argument("--face-detector", type=str,
                    default=relPath(["models"]),
                    help="path to OpenCV's deep learning face detector")
    ap.add_argument("--fd-confidence", type=float, default=0.5,
                    help="minimum probability to filter weak detections")
    ap.add_argument("--fd-label-encoder", type=str,
                    default=relPath(["models", "le.pickle"]),
                    help="path to label encoder")
    ap.add_argument("--fd-dataset", type=str,
                    default=relPath(["dataset"]),
                    help="path to input directory of faces + images")
    ap.add_argument("--fd-model", type=str,
                    default=relPath(["models", "openface_nn4.small2.v1.t7"]),
                    help="path to OpenCV's deep learning face embedding model")
    ap.add_argument("--fd-recognizer", type=str,
                    default=relPath(["models", "recognizer.pickle"]),
                    help="path to model trained to recognize faces")
    ap.add_argument("--fd-train", action="store_true",
                    help="train face recognizer on start")
    ap.add_argument("--last-faces", type=int, default=60,
                    help="show detected faces for last seconds")
    ap.add_argument("--mdclip-codec", type=str, default="mp4v", choices=["mp4v", "XVID"],
                    help="video codec")
    ap.add_argument("--mdclip-buf-length", type=int, default=10,
                    help="buffered pre motion detection clip length in seconds")
    ap.add_argument("--mdclip-max-length", type=int, default=300,
                    help="maximal after motion detection clip length in seconds")
    ap.add_argument("--mdclip-min-length", type=int, default=10,
                    help="minimal after motion detection clip length in seconds")
    ap.add_argument("--md-debounce", type=int, default=0.4,
                    help="debounce motion detection in seconds")
    ap.add_argument("--thumb-size", type=int, default=150,
                    help="thumb side size")
    ap.add_argument("--tk-queue-interval", type=int, default=50,
                    help="process tk app queue with interval in milliseconds")
    ap.add_argument("-g", "--geometry", type=str, default="800x640",
                    help="window geometry")
    ap.add_argument("-l", "--loglevel", type=int, default="20", choices=[0, 10, 20, 30, 40, 50],
                    help="log level 0:NOTSET, 10:DEBUG, 20:INFO, 30:WARNING, 40:ERROR, 50:CRITICAL")
    ap.add_argument("-s", "--source", type=str, default=0,
                    help="path to input video, camera otherwise")
    ap.add_argument("-w", "--workdir", type=str,
                    default=relPath(["datastore"]),
                    help="workdir for store images, videos")
    return ap.parse_args()


def relPath(pathItems):
    return os.path.sep.join([os.path.dirname(os.path.realpath(__file__))] + pathItems)


def loopVideo(opts=None, whileFn=lambda: True, getActionLevel=lambda: 0):

    # initialize the video stream, then allow the camera sensor to warm up
    logger.info("starting video stream")
    # vs = cv2.VideoCapture(opts["source"])
    vs = BufferedVideoStream(opts["source"], depth=opts["mdclip_buf_length"]*20)
    time.sleep(2.0)

    clipMaker = ClipMaker(vs, codec=opts["mdclip_codec"], thumbsize=opts["thumb_size"], workdir=opts["workdir"])
    faceR = FaceRecognizer(vs,
                           detector=opts["face_detector"],
                           model=opts["fd_model"],
                           recognizer=opts["fd_recognizer"],
                           labelEncoder=opts["fd_label_encoder"],
                           detectorConfidence=opts["fd_confidence"],
                           getActionLevel=getActionLevel)

    faceRec = FaceRecorder(path=opts["workdir"])
    mdState = MDState(False, None, 0, 0)
    lastFaces = []

    # loop over frames from the video file stream
    while vs.isOpened() and whileFn():
        # define the time mark of current frame
        tmark = time.monotonic()

        # grab the frame from the threaded video stream
        ok, frame = vs.read()
        if not ok:
            continue

        # resize image, then use for motion detection
        frameSized = cv2.resize(frame, (300, 300))
        mdState = detectMotion(mdState, frameSized, tmark=tmark, debounce=opts["md_debounce"])

        # store frame and draw motion icon
        if mdState.detected:
            showMotion()

            if tmark - clipMaker.startedAt >= opts["mdclip_max_length"]:
                clipMaker.stop()

            if not clipMaker.started:
                clipMaker.start()

        elif tmark - mdState.lastDetectedAt > opts["mdclip_min_length"]:
            clipMaker.stop()

        if getActionLevel() > 0:
            frm, cards = faceR.getFrameCards()
            faceRec.storeFrameCards(frm, cards)
            lastFaces[:] = updateLastFaces(lastFaces, cards, outdate=timedelta(seconds=opts["last_faces"]))
            frame = drawRecognizedFaces(frame, cards)
            frame = drawLastFaces(frame, lastFaces, dataset=opts["fd_dataset"])

        # show the output frame
        drawFrame(frame)
        time.sleep(0.02)

    # cleanup
    try:
        clipMaker.stop()
        faceRec.stop()
        faceR.stop()
        vs.release()
    except:
        pass


def drawFrame(frame):
    global tkApp
    try:
        tkApp.drawFrame(frame)
    # RuntimeError: main thread is not in main loop
    except:
        tkApp.ctrlQueue.put({"subj": "drawFrame", "frame": frame})


def showMotion():
    global tkApp
    try:
        tkApp.showMotion()
    # RuntimeError: main thread is not in main loop
    except:
        tkApp.ctrlQueue.put({"subj": "showMotion"})


def showWrite():
    global tkApp
    try:
        tkApp.showWrite()
    # RuntimeError: main thread is not in main loop
    except:
        tkApp.ctrlQueue.put({"subj": "showWrite"})


def drawRecognizedFaces(frame, cards, color=(255, 0, 0)):
    for i, card in enumerate(cards):
        # draw the bounding box of the face
        startX, startY, endX, endY = card.rect
        cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
    return frame


def drawLastFaces(frame, cards, dataset="", sort=lambda card: card.time, dims=(120, 120)):
    frameH, frameW = frame.shape[:2]
    iconH, iconW = dims
    wc = frameW // iconW
    for i, card in enumerate(sorted(cards, key=sort)[-wc:]):
        if card.name and card.name != "unknown":
            frame[0:iconH, i*iconW:(i*iconW+iconW)] = getIcon(dataset, card.name, dims)
        else:
            frame[0:iconH, i*iconW:(i*iconW+iconW)] = createIcon(card.img, dims)
        if card.name:
            cv2.putText(frame, card.name, (i*iconH+4, iconW-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 191, 255), 2)
    return frame


def updateLastFaces(lastFaces, cards, outdate=timedelta(seconds=60)):
    for card in cards:
        found = False
        for i, f in enumerate(lastFaces):
            if f.name and card.name:
                # find correspond card by name
                if f.name == card.name:
                    lastFaces[i] = card
                    found = True
                    break
            else:
                # find correspond card by area
                if cardsOverlap(f, card):
                    lastFaces[i] = card
                    found = True
                    break
        if not found:
            lastFaces.append(card)
    # remove outdated
    t0 = datetime.now()
    return [card for card in lastFaces if t0 - card.time < outdate]


def createIcon(img, dims=(300, 300)):
    # create gray blank
    blank = np.zeros((dims[0], dims[1], 3), np.uint8)
    blank[:] = (128, 128, 128)
    # place resized icon at centre of the blank
    (icoH, icoW) = img.shape[:2]
    if icoH > icoW:
        ico = imutils.resize(img, height=dims[0])
        (icoH, icoW) = ico.shape[:2]
        startX = int((dims[1]-icoW)/2)
        blank[0:dims[0], startX:startX + icoW] = ico
    else:
        ico = imutils.resize(img, width=dims[1])
        (icoH, icoW) = ico.shape[:2]
        startY = int((dims[0]-icoH)/2)
        blank[startY:startY+icoH, 0:dims[1]] = ico

    return blank


@functools.lru_cache(maxsize=32)
def getIcon(pathDataset, name, dims=(300, 300)):
    fnames = glob.glob(os.path.sep.join([pathDataset] + [name, "icon.[jp][pn][eg]*"]))
    if not fnames:
        fnames = glob.glob(os.path.sep.join([pathDataset] + [name, "*.[jp][pn][eg]*"]))
    if not fnames:
        return None
    # create gray blank
    blank = np.zeros((dims[0], dims[1], 3), np.uint8)
    blank[:] = (128, 128, 128)
    # place resized icon at centre of the blank
    ico = cv2.imread(fnames[0])
    (icoH, icoW) = ico.shape[:2]
    if icoH > icoW:
        ico = imutils.resize(ico, height=dims[0])
        (icoH, icoW) = ico.shape[:2]
        startX = int((dims[1]-icoW)/2)
        blank[0:dims[0], startX:startX + icoW] = ico
    else:
        ico = imutils.resize(ico, width=dims[1])
        (icoH, icoW) = ico.shape[:2]
        startY = int((dims[0]-icoH)/2)
        blank[startY:startY+icoH, 0:dims[1]] = ico

    return blank


def detectMotion(mdState, frame, tmark=0, debounce=0.04):
    if tmark == 0:
        tmark = time.monotonic()
    # debounce motion detection
    if not mdState.detected or (tmark - mdState.trackedAt) > debounce:
        # https://medium.com/@pytholabs/motion-detector-alarmusing-opencv-python-b3ff21c69e0c
        # convert to gray-scale and add gaussian blur to reduce noise
        frame1 = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
        if mdState.trackedFrame is not None:
            frameDelta = cv2.absdiff(frame1, mdState.trackedFrame)
            # apply a threshold function to suppress the smaller values below 25 which will yield a matrix with binary values
            td = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
            if(td.sum() > 100):
                mdState = MDState(True, frame1, tmark, tmark)
            else:
                mdState = MDState(False, frame1, tmark, mdState.lastDetectedAt)
        else:
            mdState = MDState(False, frame1, tmark, mdState.lastDetectedAt)
    return mdState


def main():
    opts = vars(getCLIArgs())
    logging.basicConfig(level=opts["loglevel"])
    logger.info("start with %s", json.dumps(opts, indent=4))

    if opts["fd_train"]:
        logger.info("train face recognizer")
        extractEmbeddings(dataset=opts["fd_dataset"],
                          detector=opts["face_detector"],
                          embeddings=os.path.sep.join([opts["face_detector"], "embeddings.pickle"]),
                          model=opts["fd_model"],
                          detectorConfidence=opts["fd_confidence"])
        trainModel(embeddings=os.path.sep.join([opts["face_detector"], "embeddings.pickle"]),
                   recognizer=opts["fd_recognizer"],
                   labelEncoder=opts["fd_label_encoder"])
    else:
        time.sleep(2.0)

    global tkApp
    tkApp = TkApp(opts=opts)
    tkApp.run()
    videoThread = threading.Thread(target=loopVideo, args=(
        opts,
        lambda: tkApp.running,
        lambda: tkApp.actionLevel if tkApp.tglMonitor else 0
    ))
    videoThread.start()
    tkApp.eventLoop()


if __name__ == "__main__":
    main()
