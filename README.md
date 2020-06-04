# myHome-Doorcam

Welcome to the myHome Doorcam project.

The Doorcam is a replacement for video doorbells that invade your privacy.

Using off-the-shelf hardware the Doorcam will do all of the usual stuff, such as capturing video on motion events, as well as more advanced stuff, like face-detection.  

Getting Started
---------------
To get started you will need a few things:
First of all, I have a lot of work to do on the install.  The setup for the working prototypes is based on Adrian's setup of OpenCV on PyImageSearch.  If you have that set up then the project _should_ work after cloning it from Git.  Also, adding the preload to your bashrc may _not_ be necessary if you follow along on PyImageSearch and get past it there.

Stay tuned for this to be updated soon.


1. Clone the project 
````
mkdir $HOME/livefree && cd $HOME/livefree
git clone https://github.com/LiveFreeOrDieSoftware/myHome-Doorcam.git
````

2. [Raspberry Setup](./SETUP.md)

3. Running
````
    cd viewer
    python viewer-tk.py
````    

4. [DoorCam Viewer Usage](./viewer/README.md)
