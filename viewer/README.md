# MyHome DoorCam Viewer

MyHome DoorCam Viewer with Face Detection, Motion Detection, Face Recognition, Face Training, Image and Video Review

## Usage

Optional Parameters:
```
  -h, --help            show this help message and exit

  --action {0,1,2}
    action level    0:motion detection,
                    1:face detection,
                    2:face recognition
    default: face detection

  --face-detector FACE_DETECTOR

    path to OpenCV's deep learning face detector
    default: ./models

  --fd-confidence FD_CONFIDENCE

    minimum probability to filter weak detections
    default: 0.5

  --fd-label-encoder FD_LABEL_ENCODER

    path to label encoder
    default: ./models/le.picle

  --fd-dataset FD_DATASET

    path to input directory of faces + images
    default: ./dataset

  --fd-model FD_MODEL

    path to OpenCV's deep learning face embedding model
    default: ./models/openface_nn4.small2.v1.t7

  --fd-recognizer FD_RECOGNIZER

    path to model trained to recognize faces
    default: ./models/recognizer.pickle

  --fd-train

    train face recognizer on start
    default: false

  --last-faces LAST_FACES

    show detected faces for last seconds
    default: 60 s

  --mdclip-codec {mp4v,XVID}

    video codec
    default: mp4v

  --mdclip-buf-length MDCLIP_BUF_LENGTH

    buffered pre motion detection clip length in seconds
    default: 10 s

  --mdclip-max-length MDCLIP_MAX_LENGTH

    maximal after motion detection clip length in seconds
    default: 300 s

  --mdclip-min-length MDCLIP_MIN_LENGTH

    minimal after motion detection clip length in seconds
    default: 10 s

  --md-debounce MD_DEBOUNCE

    debounce motion detection in seconds
    default: 0.4 s

  --thumb-size THUMB_SIZE

    thumb side size
    default: 150 pixels

  --tk-queue-interval TK_QUEUE_INTERVAL

    process tk app queue with interval in milliseconds
    default: 50 ms

  -g GEOMETRY
  --geometry GEOMETRY

    window geometry resolution
    default: 800x640

  -l {0,10,20,30,40,50}
  --loglevel {0,10,20,30,40,50}

    log level  0:NOTSET
              10:DEBUG
              20:INFO
              30:WARNING
              40:ERROR
              50:CRITICAL
    default: INFO

  -s SOURCE
  --source SOURCE

    path to input video, camera otherwise

  -w WORKDIR
  --workdir WORKDIR

    working directory path to store images, videos
    default: ./datastore
```

## Reference

* https://stackoverflow.com/questions/28327020/opencv-detect-mouse-position-clicking-over-a-picture

* https://www.pyimagesearch.com/2016/05/23/opencv-with-tkinter/

* https://stackoverflow.com/questions/459083/how-do-you-run-your-own-code-alongside-tkinters-event-loop
