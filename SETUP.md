# Step-by-Step Setup for Raspberry Pi

This guide was written based on the first version of Raspberry Pi OS (32-bit) with desktop (formerly known as Raspbian), releaseed May 2020.
The version is NOT 'Lite' and does not come with 'recommended software', and can be found [here](https://www.raspberrypi.org/downloads/raspberry-pi-os/).

1. Start with a [fresh image](https://downloads.raspberrypi.org/raspios_armhf_latest) of Buster, Raspberry Pi OS with desktop (May 2020).
After burning the image you may want to also add `wpa_supplicant.conf` and `ssh` to `/boot`. For information on setting up the Raspberry Pi search around for some guides.  (More to come on this later, here, but skimping for now.)
2. Go through the initial setup wizard on first boot. It will remind you to update the password from default and then tell you 'there are a few things to set up':
  - Update Country, Language & Timezone
  - Update Password
  - Set up Screen, if there is a 'border'. (With the Official RPi 7" Touchscreen you should just need to click 'Next'.)
  - Select Wireless Network. (If you added a wpa_supplicant.conf you will not need to enter the password, otherwise you will.)
  - Update Sfotware:  select 'Next' and let it update; this could take a while.
  - Restart

After the RPi restarts, open a terminal window.

2. Run raspi-config and enable interfaces:
  - `$ sudo raspi-config'
    - Go down to item #5, Interfacing Options
    - Select Camera, and enable
    - Optional: return to Interfacing Options and enable VNC
    - SSH should already be enabled if we added a file named `ssh` to `/boot`
  - Reboot

3. Make Python3 the default version of Python:
```
$ sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
$ update-alternatives --list python
```
The last command should return `/usr/bin/python3`, which shows python3 is now the default.

The result of the second command should be to output `/usr/bin/python3`, showing that Python3 is now the default version and is called by the command `python`.

4. Get the Project:
```
$ mkdir $HOME/livefree && cd $HOME/livefree
$ git clone https://github.com/LiveFreeOrDieSoftware/myHome-Doorcam.git
```
Change in to the project directory: `$ cd myHome-Doorcam`.

5. Install dependencies:
```
$ chmod +x install_dependencies.sh
$ ./install_dependencies.sh
```
Note that there this is a VERY simple script. You will need to watch and be sure it completes correctly, that there are no errors, and that the packages are installed correctly.

6. Get the Python package installer, PIP:
```
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
```
Because we set the default verion of Python to Python3 this should install the correct versions.

7. Install support for Python virtual environments:
```
sudo pip install virtualenv virtualenvwrapper
```

9. Update bashrc, or run `update_bashrc.sh`
These lines are necessary in your profile to set up the environment to run the Python virtual environments. You can either use the script (`chmod +xor edit `.bashrc` by hand. These _should_ be in place _before_ creating your virtual environment
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
You should see a bunch of output from virtualenvwrapper.user_scripts.

11. Create the Python virtual environment:
```
mkvirtualenv cv -p python3
```
There will be output from this command and, if successful, the prompt should change to:
```
(cv) user@hostname:~/livefree/myHome-Doorcam $ 
```

12. Install Python requirements in the virutal environment:
```
(cv)$ pip install -r requirements.txt
```

13. Launch the myHome Doorcam:
```
$ cd viewer
$ python viewer-tk.py
```

**NOTE**
If you reboot, or work from a different terminal window, you **MUST** be in the CV virtualenv for the viewer to work.
To invoke the CV virtualenv and launch the viewer use the following commands:
```
$ workon cv
(cv) $ cd $HOME/livefree/myHome-Doorcam/viewer
(cv) $ python viewer-tk.py
```
After you have done that you can launch the viewer.
