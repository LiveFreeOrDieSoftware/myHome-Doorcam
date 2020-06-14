# Step-by-Step Setup for Raspberry Pi

This guide was written based on the first version of Raspberry Pi OS (32-bit) with desktop, releaseed May 2020.
The version is NOT 'Lite' and does not come with 'recommended software', found [here](https://www.raspberrypi.org/downloads/raspberry-pi-os/).

1. Start with a [fresh image](https://downloads.raspberrypi.org/raspios_armhf_latest) of Buster, Raspberry Pi OS with desktop (May 2020)
2. Go through the initial startup wizard:
- update locale
- update timezone
- update software
- reboot

3. Make Python3 the default version of Python:
```
$ sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
$ update-alternatives --list python
```

4. Get the Project:
```
$ mkdir $HOME/livefree && cd $HOME/livefree
$ git clone https://github.com/LiveFreeOrDieSoftware/myHome-Doorcam.git
```

5. Install dependencies:
```
$ ./install_dependencies.sh
```

6. Get the Python package installer, PIP:
```
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
```

7. Install support for Python virtual environments:
```
sudo pip install virtualenv virtualenvwrapper
```

9. Update bashrc, or run `update_bashrc.sh`
These lines are necessary in your profile to set up the environment to run the Python virtual environments. You can either use the script or edit `.bashrc` by hand. These _should_ be in place _before_ creating your virtual environment
Edit ~/.bashrc, add:
```
# virtualenv and virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin
```

10. Invoke the new settings:
```
$ source ~/.bashrc
```

11. Create the Python virtual environment:
```
mkvirtualenv cv -p python3
```

12. Install Python requirements in the virutal environment:
```
(cv)$ pip install -r requirements.txt
```

13. Launch the myHome Doorcam:

