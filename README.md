# myHome-Doorcam

Welcome to the myHome Doorcam project.

The Doorcam is a replacement for video doorbells that invade your privacy.

Using off-the-shelf hardware the Doorcam will do all of the usual stuff, such as capturing video on motion events, as well as more advanced stuff, like face-detection.  

Getting Started
---------------
To get started you will need a few things:
- A Raspberry Pi: a model 4 is recommended, but this also has been tested on a 3 B+. Note that the Pi will be kept pretty busy and may require active cooling.  On a 3 B+ I was running in to issues with thermal warnings and freezing up. The 4 will run even hotter.
- a RPi camera: this project was tested with cameras attached though the RPi camera interface.  USB cameras have not been tested. An extended flex-cable will allow you to deploy the camera at a distance from the screen; i.e. outside the doorway, with the screen/Pi inside.  Stay tuned for 3d printable camera housings that will be posted with the project.
- Screen: the project is intended to use the 7" touchscreen, so that it could be deployed at an entranceway door. Other monitors have not been tested, yet.
- PiR sensor: A PiR sensor can be used to wake the screen on approach, so that when you walk up to the door the screen will activate, and you will see a live stream from the camera.

Once you have assembled the hardware, you will need a freshly imaged SD card with the most recent version of the Raspberry Pi OS Debian variant of Buster. (Most recently tested with the RPi OS relesed May 2020.)

Once  you have your hardware assembled continue on to the SETUP.md page for installation instructions.
