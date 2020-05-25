import subprocess, time, datetime

motionDetectionEnabled = True

try:
    from gpiozero import MotionSensor
    import RPi.GPIO as GPIO
except ImportError:
    motionDetectionEnabled = False

PIR_PIN = 4
SCREEN_SAVER_TIMEOUT_SECONDS = 0
lastMotionDetected = datetime.datetime.now() - datetime.timedelta(days=1)


def motion_handler(pin):
    global lastMotionDetected
    print ('Motion Detected!')
    seconds = (datetime.datetime.now() - lastMotionDetected).total_seconds()
    print('secs = ', seconds)
    if seconds > SCREEN_SAVER_TIMEOUT_SECONDS:
        print('Resetting motion detector ...', seconds)
        subprocess.call('xset dpms force on', shell=True)
        lastMotionDetected = datetime.datetime.now()


if motionDetectionEnabled:
    pir = MotionSensor(PIR_PIN)
    GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=motion_handler)

# while True:
#     if motionDetectionEnabled and pir.motion_detected:
#         print('Motion Detected')
#         seconds = (datetime.datetime.now() - lastMotionDetected).total_seconds()
#         print('secs = ', seconds)
#         if seconds > SCREEN_SAVER_TIMEOUT_SECONDS:
#             print('Resetting motion detector ...', seconds)
#             subprocess.call('xset dpms force on', shell=True)
#             lastMotionDetected = datetime.datetime.now()
#     time.sleep(2)

while True:
    print("wait loop simulating busy computer...")
    time.sleep(10)
