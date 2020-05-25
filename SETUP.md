# Setup for Raspberry Pi
```
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
update-alternatives --list python
python
workon cv
mkvirtualenv cv
pip --version
apt list --installed
apt list --installed | grep libhdf5
apt list python*opencv*
apt show python3-opencv

sudo apt-get update && sudo apt-get upgrade
sudo apt-get install libjpeg-dev libtiff5-dev libjasper-dev libpng-dev
sudo apt-get install build-essential cmake pkg-config
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install libxvidcore-dev libx264-dev
sudo apt-get install libgdk-pixbuf2.0-dev libpango1.0-dev
sudo apt-get install libgtk2.0-dev libgtk-3-dev
sudo apt-get install libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt-get install libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt-get install libcblas-dev
sudo apt-get install libhdf5-dev
sudo apt-get install libhdf5-serial-dev
sudo apt-get install libatlas-base-dev
sudo apt-get install libcblas-dev
```
# might only need these commands
```
pip3 install opencv-python
sudo apt-get install -y libcblas-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev  libqtgui4  libqt4-test
sudo apt-get install libatlas-base-dev
# add this to your .bashrc
LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1 python demo.py 
pip install imutils
pip install sklearn
``` 
